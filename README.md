# Flotsam Türkçe Yama

Flotsam'ın Epic Games sürümü için 3.197 dil girdisini kapsayan gayriresmî Türkçe çeviri.

Çeviri, oyunun İngilizce metinlerinden Codex ve yardımcı ajanlarla hazırlanmıştır. Mevcut topluluk çevirisi kaynak olarak kullanılmamış; Google Translate veya başka bir harici makine çevirisi hizmeti kullanılmamıştır. Karakter konuşmaları, görevler, başarımlar, menüler ve rehber metinleri kapsanır. Font kimlikleri, oyun değişkenleri ve özel adlar gerektiği yerde korunur.

**Sürüm:** 1.0.0 · **Tarih:** 7 Kasım 2026 · **Platform:** Windows / Epic Games

## İndir ve kur

1. [Releases sayfasından](https://github.com/smhguler/Flotsam-Turkce-Yama/releases/latest) `Flotsam-Turkce-Yama-v1.0.0.zip` dosyasını indirip bir klasöre çıkart.
2. Oyunu kaydedip kapat.
3. Çıkarttığın klasörde PowerShell aç. Oyunun Program Files klasöründe olması nedeniyle yönetici olarak açman gerekebilir.
4. Şu komutu çalıştır:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Kur.ps1
```

Varsayılan oyun konumu `C:\Program Files\Epic Games\Flotsam`. Farklı bir konum için:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Kur.ps1 -OyunKlasoru "D:\Epic Games\Flotsam"
```

5. Oyunu **Epic Games üzerinden** aç. **Ayarlar > Dil > Türkçe** seç.

Kurulum çevrimdışı çalışır; Python, BepInEx veya çeviri servisi gerektirmez. Yalnızca `Flotsam_Data\resources.assets` dosyasını değiştirir. Kayıt dosyalarına dokunmaz.

## Uyumluluk ve doğrulama

Bu sürüm, hazırlama sırasında doğrulanan Epic Games oyun dosyasıyla eşleşir. Farklı sürüme, güncellenmiş dosyaya veya başka bir yamaya otomatik olarak uygulanmaz. Sürüm kararı dosya adına göre değil SHA-256 özetine göre verilir. Steam ve GOG sürümleri doğrulanmamıştır.

| Dosya | SHA-256 |
| --- | --- |
| Desteklenen orijinal `resources.assets` | `2b8ed949fb1ada4d4f4af2b1dc10db9bd24df987826d0780600cc566d1170f71` |
| Türkçe `resources.assets` | `00cafa58abb6dca798ffc16207143bc8985be06b5814dee48224a40f2f57f935` |

Paket tam oyun dosyasını içermez. Yaklaşık 314 KB'lık fark yaması, kendi kurulu oyun dosyandan Türkçe dosyayı üretir. Kurulumdan önce ve sonra dosya özetleri kontrol edilir; orijinal dosya `Flotsam_Data\resources.assets.flotsam-tr.bak` olarak saklanır.

Çeviri dosyasında boş girdi kalmadığı, değişkenlerin ve biçimlendirme kodlarının korunduğu, diğer dillerin değişmediği ve diğer 23.561 Unity nesnesinin aynı kaldığı kontrol edilmiştir. Oyunun tamamı görsel olarak oynanıp test edilmemiştir; anlam veya taşma sorunları bildirebilirsin.

## Geri alma

Oyunu kapatıp aynı klasörde çalıştır:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Geri_Al.ps1
```

Özel oyun konumu için `-OyunKlasoru` parametresini ekle. Betik yalnızca bu yamayla eşleşen dosyayı, doğrulanan yedekten geri yükler. Sonradan güncellenmiş bir dosyanın üstüne yazmaz. Epic Games dosya doğrulaması da orijinal oyun dosyasını geri getirebilir; oyun güncellemeleri yamayı kaldırabilir.

## Çeviriye katkı

Türkçe kaynak `translations/tr.json` dosyasında. Kayıtların sırasını, `anahtar` değerlerini ve metindeki `<...>`, `{[...]}`, `%...%` gibi oyun kodlarını koru. Aynı anahtar oyunun tablosunda birden fazla kez bulunabilir; bu yüzden kaynak dosya sıralı bir listedir.

Bir sorunu [Issues](https://github.com/smhguler/Flotsam-Turkce-Yama/issues) üzerinden bildirirken ekranda görünen cümleyi, nerede çıktığını ve önerdiğin karşılığı yaz. Ekran görüntüsü de ekleyebilirsin.

## Yamayı yeniden oluşturma

Python 3.10 veya üzeri yeterlidir; ek paket gerekmez. Orijinal oyun dosyasını depoya ekleme.

```powershell
python .\tools\build_patch.py "C:\oyun-yedegi\resources.assets"
python -m unittest discover -s tests -v
```

Derleyici desteklenen orijinal dosyayı kontrol eder, Türkçe tabloyu oluşturur ve küçük fark yamasını üretir. Yeni bir çeviri sürümü hazırlarken `Yama.ps1` içindeki hedef ve yama özetlerini yeni `release.json` değerleriyle güncelle; sürüm numarasını ve sürüm notlarını da değiştir.

## Haklar ve hazırlama bilgisi

Flotsam ve orijinal oyun içerikleri Pajama Llama Games ve ilgili hak sahiplerine aittir. Bu proje resmî değildir ve onlarla bağlantılı değildir. Yama, sahip olduğun oyun kurulumunu gerektirir. Oyun çalıştırılabilir dosyaları, tam veri paketleri, kullanıcı kayıtları veya hesap bilgileri bu depoya dahil değildir.

Paylaşan: [smhguler](https://github.com/smhguler). Çeviri ve araç hazırlama desteği: Codex.
