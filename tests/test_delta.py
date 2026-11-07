import base64
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_patch', ROOT / 'tools/build_patch.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class DeltaTests(unittest.TestCase):
    def setUp(self):
        self.source = bytes(range(256)) * 512
        self.edits = [(0, 4, b'New header'), (500, 504, 'Türkçe: ğüşöçıİ'.encode()),
                      (1000, 1008, b''), (len(self.source), len(self.source), b'tail')]
        self.operations = builder.make_operations(self.source, self.edits)
        self.expected = b''.join(self.source[op[1]:op[1] + op[2]] if op[0] == 0
                                 else base64.b64decode(op[1]) for op in self.operations)
        self.patch = dict(format='flotsam-delta-v1', source_sha256=builder.sha(self.source),
                          source_size=len(self.source), target_sha256=builder.sha(self.expected),
                          target_size=len(self.expected), operations=self.operations)

    def test_round_trip_with_growth_deletion_and_utf8(self):
        self.assertEqual(builder.apply_delta(self.source, self.patch), self.expected)

    def test_wrong_game_version_is_rejected(self):
        with self.assertRaises(ValueError):
            builder.apply_delta(b'wrong version', self.patch)

    def test_out_of_bounds_copy_is_rejected(self):
        bad = copy.deepcopy(self.patch)
        bad['operations'][0] = [0, -1, 4]
        with self.assertRaises(ValueError):
            builder.apply_delta(self.source, bad)

    def test_truncated_copy_is_rejected(self):
        bad = copy.deepcopy(self.patch)
        bad['operations'][0] = [0, len(self.source) - 1, 99]
        with self.assertRaises(ValueError):
            builder.apply_delta(self.source, bad)

    def test_modified_translation_is_rejected(self):
        bad = copy.deepcopy(self.patch)
        bad['operations'][0] = [1, base64.b64encode(b'damaged').decode()]
        with self.assertRaises(ValueError):
            builder.apply_delta(self.source, bad)

    def test_output_size_limit_is_enforced(self):
        bad = copy.deepcopy(self.patch)
        bad['target_size'] = 1
        with self.assertRaises(ValueError):
            builder.apply_delta(self.source, bad)

    def test_overlapping_edits_are_rejected(self):
        with self.assertRaises(ValueError):
            builder.make_operations(self.source, [(1, 10, b'a'), (8, 12, b'b')])

    def test_unknown_operation_is_rejected(self):
        bad = copy.deepcopy(self.patch)
        bad['operations'][0] = [99, 'invalid']
        with self.assertRaises(ValueError):
            builder.apply_delta(self.source, bad)


if __name__ == '__main__':
    unittest.main()
