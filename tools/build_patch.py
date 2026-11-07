"""Build the distributable translation delta from an owned, original game file.

Python standard library only. Original game data is referenced by COPY operations;
the patch embeds Turkish strings and the few changed Unity metadata bytes.
"""
import argparse
import base64
import gzip
import hashlib
import json
import re
import struct
from pathlib import Path

ORIGINAL_SHA256 = '2b8ed949fb1ada4d4f4af2b1dc10db9bd24df987826d0780600cc566d1170f71'
TOKEN = re.compile(r'<[^>]+>|\{[^{}]*\}|%[^%\s]+%|\[[^\]\r\n]+\]')


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Reader:
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def read(self, fmt):
        size = struct.calcsize(fmt)
        values = struct.unpack_from(fmt, self.data, self.pos)
        self.pos += size
        return values[0] if len(values) == 1 else values

    def align(self, size=4):
        self.pos = (self.pos + size - 1) // size * size

    def string(self):
        length = self.read('<i')
        if not 0 <= length <= 1_000_000:
            raise ValueError('Invalid string size')
        value = self.data[self.pos:self.pos + length].decode('utf-8')
        self.pos += length
        self.align()
        return value


def serialized_string(value):
    data = value.encode('utf-8')
    return struct.pack('<i', len(data)) + data + b'\0' * (-len(data) % 4)


def unity_objects(data):
    if struct.unpack_from('>I', data, 8)[0] != 22 or data[16] != 0:
        raise ValueError('Unsupported Unity file format')
    data_offset = struct.unpack_from('>Q', data, 32)[0]
    reader = Reader(data, 48)
    reader.pos = data.index(b'\0', reader.pos) + 1
    reader.read('<i')  # platform
    if reader.read('<?'):
        raise ValueError('This build expects stripped type trees')
    type_count = reader.read('<i')
    for _ in range(type_count):
        class_id = reader.read('<i')
        reader.pos += 3  # is_stripped and script_type_index
        reader.pos += 32 if class_id == 114 else 16
    objects = {}
    count = reader.read('<i')
    if not 0 < count < 100_000:
        raise ValueError('Invalid Unity object count')
    for _ in range(count):
        reader.align()
        record = reader.pos
        path_id, start, size, type_id = reader.read('<qqIi')
        objects[path_id] = (start + data_offset, size, record)
    return objects


def translation_edits(original, translations):
    objects = unity_objects(original)
    start, old_size, _ = objects[19631]
    reader = Reader(original, start + 60)
    if struct.unpack_from('<i', original, start + 56)[0] != 3197:
        raise ValueError('Unexpected translation table')
    if not isinstance(translations, list) or len(translations) != 3197:
        raise ValueError('Expected the complete 3197-row translation list')
    edits = []
    from collections import Counter
    for row_index in range(3197):
        key = reader.string()
        entry = translations[row_index]
        if entry['anahtar'] != key:
            raise ValueError('Translation keys/order do not match this game build')
        reader.read('<i')  # term type
        if reader.read('<i') != 15:
            raise ValueError('Unexpected language count')
        english = None
        for index in range(15):
            before = reader.pos
            value = reader.string()
            if index == 0:
                english = value
            if index == 13:
                translated = entry['turkce']
                if not isinstance(translated, str) or not translated.strip():
                    raise ValueError('Empty translation: ' + key)
                if Counter(TOKEN.findall(english)) != Counter(TOKEN.findall(translated)):
                    raise ValueError('Changed control or formatting codes: ' + key)
                if re.findall(r'<term>(.*?)</term>', english) != re.findall(r'<term>(.*?)</term>', translated):
                    raise ValueError('Changed term identifier: ' + key)
                new = serialized_string(translated)
                if new != original[before:reader.pos]:
                    edits.append((before, reader.pos, new))
        flag_count = reader.read('<i')
        reader.pos += flag_count
        reader.align()
        reader.string()  # term description
    old_name = serialized_string('Türkçe (Topluluk Çeviri)')
    raw = original[start:start + old_size]
    if raw.count(old_name) != 1:
        raise ValueError('Unexpected Turkish language name')
    name_start = start + raw.index(old_name)
    edits.append((name_start, name_start + len(old_name), serialized_string('Türkçe')))
    return sorted(edits)


def make_operations(original, edits):
    operations, cursor = [], 0
    for begin, end, new in edits:
        if not cursor <= begin <= end <= len(original):
            raise ValueError('Overlapping or invalid edit')
        if begin > cursor:
            operations.append([0, cursor, begin - cursor])
        if new:
            operations.append([1, base64.b64encode(new).decode('ascii')])
        cursor = end
    if cursor < len(original):
        operations.append([0, cursor, len(original) - cursor])
    return operations


def build_operations(original, edits):
    """Reproduce the verified Unity layout: path-id order and 8-byte alignment."""
    objects = unity_objects(original)
    data_offset = struct.unpack_from('>Q', original, 32)[0]
    i2_start, i2_size, _ = objects[19631]
    i2_edits = [(begin - i2_start, end - i2_start, new)
                for begin, end, new in edits if i2_start <= begin < i2_start + i2_size]
    i2_ops = make_operations(original[i2_start:i2_start + i2_size], i2_edits)
    i2_new_size = sum(op[2] if op[0] == 0 else len(base64.b64decode(op[1])) for op in i2_ops)
    metadata = bytearray(original[:data_offset])
    data_ops, cursor = [], 0
    for object_id in sorted(objects):
        start, old_size, record = objects[object_id]
        size = i2_new_size if object_id == 19631 else old_size
        struct.pack_into('<qI', metadata, record + 8, cursor, size)
        if object_id == 19631:
            data_ops += [[0, op[1] + start, op[2]] if op[0] == 0 else op for op in i2_ops]
        else:
            data_ops.append([0, start, size])
        pad = (-size) % 8
        if pad:
            if original[start + old_size:start + old_size + pad] == b'\0' * pad:
                data_ops.append([0, start + old_size, pad])
            else:
                data_ops.append([1, base64.b64encode(b'\0' * pad).decode('ascii')])
        cursor += size + pad
    struct.pack_into('>Q', metadata, 24, data_offset + cursor)
    prefix = 0
    while prefix < data_offset and metadata[prefix] == original[prefix]:
        prefix += 1
    suffix = data_offset
    while suffix > prefix and metadata[suffix - 1] == original[suffix - 1]:
        suffix -= 1
    all_ops = make_operations(original[:data_offset], [(prefix, suffix, bytes(metadata[prefix:suffix]))]) + data_ops
    merged = []
    for op in all_ops:
        if merged and merged[-1][0] == op[0] == 0 and merged[-1][1] + merged[-1][2] == op[1]:
            merged[-1][2] += op[2]
        else:
            merged.append(op)
    return merged


def apply_delta(original, patch):
    if patch.get('format') != 'flotsam-delta-v1':
        raise ValueError('Unsupported patch format')
    if len(original) != patch['source_size'] or sha(original) != patch['source_sha256']:
        raise ValueError('Wrong original game file')
    target_size = patch['target_size']
    if not isinstance(target_size, int) or not 0 < target_size <= 80_000_000:
        raise ValueError('Invalid output size')
    operations = patch['operations']
    if not isinstance(operations, list) or not 0 < len(operations) <= 100_000:
        raise ValueError('Invalid operation count')
    output = bytearray()
    for operation in operations:
        if operation[0] == 0 and len(operation) == 3:
            start, length = operation[1:]
            if not isinstance(start, int) or not isinstance(length, int) or not 0 <= start <= len(original) or not 0 <= length <= len(original) - start:
                raise ValueError('Invalid COPY range')
            output += original[start:start + length]
        elif operation[0] == 1 and len(operation) == 2:
            output += base64.b64decode(operation[1], validate=True)
        else:
            raise ValueError('Invalid delta operation')
        if len(output) > target_size:
            raise ValueError('Output exceeds declared size')
    if len(output) != target_size or sha(output) != patch['target_sha256']:
        raise ValueError('Output verification failed')
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--translations', type=Path, default=Path(__file__).resolve().parents[1] / 'translations/tr.json')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'patch/flotsam-tr-v1.0.0.json.gz')
    parser.add_argument('--expect-target', help='Optional SHA-256 of an independently verified translated file')
    args = parser.parse_args()
    original = args.original.read_bytes()
    if sha(original) != ORIGINAL_SHA256:
        raise SystemExit('Unsupported original resources.assets file')
    translations = json.loads(args.translations.read_text(encoding='utf-8'))
    edits = translation_edits(original, translations)
    operations = build_operations(original, edits)
    output = bytearray()
    for op in operations:
        output += original[op[1]:op[1] + op[2]] if op[0] == 0 else base64.b64decode(op[1])
    target_hash = sha(output)
    if args.expect_target and target_hash != args.expect_target.lower():
        raise SystemExit('Independent target hash mismatch: ' + target_hash)
    patch = dict(format='flotsam-delta-v1', source_sha256=sha(original),
                 source_size=len(original), target_sha256=target_hash,
                 target_size=len(output), operations=operations)
    assert apply_delta(original, patch) == output
    packed = gzip.compress(json.dumps(patch, separators=(',', ':')).encode(), mtime=0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(packed)
    release = dict(version='1.0.0', date='2026-11-07', translation_entries=len(translations),
                   game_store='Epic Games', unity_version='6000.3.26f1',
                   source_sha256=sha(original), source_size=len(original),
                   target_sha256=target_hash, target_size=len(output),
                   patch_sha256=sha(packed), patch_size=len(packed))
    (args.output.parent.parent / 'release.json').write_text(json.dumps(release, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(release, indent=2))


if __name__ == '__main__':
    main()
