# Toplantı Asistanı

Zamanla fiziksel bir ses yakalama cihazını bilgisayar tarafındaki AI işlemeyle birleştirecek bir toplantı sesi projesi.

Bu README, projeyi ilk kez açan birinin kurulumdan manuel teste kadar her adımı sırayla uygulayabileceği bir rehberdir. Komutlar Windows PowerShell 5.1 ile uyumludur.

## 1. Proje Özeti

Proje ilk geliştirme milestone'unda: kayıtlı sesten speaker diarization. Kullanıcı onayıyla bunun üzerine konuşmacılı transkript eklendi.

Mevcut akış:

```text
Ses dosyası (WAV/FLAC)
  → speaker diarization (pyannote)
  → Speech-to-Text (Whisper Turbo, Türkçe)
  → konuşmacı / metin eşleştirme
  → JSON çıktı
  → yerel FastAPI (POST /diarize)
```

Konuşmacılar gerçek isimlerle değil, `SPEAKER_00`, `SPEAKER_01`, `SPEAKER_02` gibi anonim etiketlerle gösterilir. Etiketler, konuşmacıların kayıtta ilk konuşma sırasına göre verilir.

Ayrıntılı durum ve ölçümler için `CURRENT_STATE.md`, alınan kararlar için `DECISIONS.md` dosyasına bakın.

## 2. Mevcut Özellikler

- Speaker diarization (`pyannote/speaker-diarization-community-1`)
- Türkçe Speech-to-Text
- Whisper Turbo
- CPU / CUDA otomatik cihaz seçimi
- Konuşmacı + zaman + metin içeren JSON çıktısı
- Yerel FastAPI backend
- Swagger arayüzü (`/docs`)
- `outputs/` klasörüne JSON sonuç kaydı
- Yüklenen orijinal ses dosyası işlem sonrası silinir, kalıcı olarak saklanmaz

Henüz kapsamda olmayanlar: gerçek zamanlı streaming, UI, veritabanı, cihaz iletişimi, konuşmacı kimliği tanıma, toplantı özetleri ve LLM özellikleri.

## 3. Gereksinimler

- **Python** 3.10 veya üzeri (3.13 ile doğrulandı)
- **`uv`** paket yöneticisi: https://docs.astral.sh/uv/ (Windows'ta `winget install astral-sh.uv` ile kurulabilir)
- **Git**
- **Hugging Face hesabı**
- **`pyannote/speaker-diarization-community-1` model erişimi** (bkz. bölüm 5)
- **İnternet bağlantısı:** ilk kurulum ve ilk çalıştırmadaki model indirmeleri için
- **Disk alanı:** birkaç GB (CUDA'lı PyTorch ve Whisper Turbo modeli için)
- **NVIDIA GPU (isteğe bağlı):**
  - CUDA varsa GPU kullanılır ve işlem çok daha hızlıdır. Ayrıca CUDA Toolkit kurmak gerekmez; güncel bir NVIDIA sürücüsü yeterlidir.
  - GPU yoksa proje CPU ile çalışır, yalnızca daha yavaştır.

## 4. Ortam Kurulumu

Projeyi klonlayıp bağımlılıkları kurun:

```powershell
git clone https://github.com/KeremGerede/Toplanti_sistemi.git
cd Toplanti_sistemi
uv sync
```

Windows ve Linux'ta PyTorch'un CUDA 12.8 build'i kurulur. Bu build GPU olmayan makinede de CPU ile çalışır.

CUDA kontrolü:

```powershell
uv run python -c "import torch; print(torch.cuda.is_available())"
```

- `True` → CUDA kullanılabilir; sistem GPU ile çalışır.
- `False` → sistem CPU ile çalışabilir.

## 5. Hugging Face Erişimi

Diarization modeli gated'dir; kullanmadan önce erişim izni gerekir.

1. https://huggingface.co adresinde Hugging Face hesabınıza giriş yapın.
2. https://huggingface.co/pyannote/speaker-diarization-community-1 model sayfasındaki kullanım koşullarını kabul edin.
3. https://hf.co/settings/tokens adresinden **Read** yetkili bir token oluşturun.
4. Terminalde güvenli şekilde giriş yapın:

   ```powershell
   uv run hf auth login
   ```

   Token gizli bir girişle istenir ve repo dışında, kullanıcı klasörünüzde saklanır.

Giriş kontrolü. Bu komut Hugging Face kullanıcı adınızı yazdırmalıdır:

```powershell
uv run python -c "from huggingface_hub import whoami; print(whoami()['name'])"
```

Alternatif olarak token, Windows "Ortam Değişkenleri" penceresinden kullanıcı düzeyinde `HF_TOKEN` olarak tanımlanabilir. Bunu komut satırından yapmayın; token komut geçmişine düşer.

### Token güvenliği

Token hiçbir zaman şu yerlere yazılmamalıdır:

- README'ye
- Python koduna
- GitHub reposuna
- commit geçmişine

### Model indirme notları

- Diarization modeli ilk kullanımda Hugging Face cache'ine iner. Sonraki çalıştırmalar `HF_HUB_OFFLINE=1` ile çevrimdışı yapılabilir.
- Windows'taki Hugging Face "symlink" uyarısı zararsızdır; `HF_HUB_DISABLE_SYMLINKS_WARNING=1` ile susturulabilir.

## 6. Manuel Test Sesini Hazırlama

İlk manuel test için şu dosya gereklidir:

```text
tests/data/two_speakers_clean.wav
```

Önerilen kayıt:

- Yaklaşık 30–60 saniye
- 2 farklı kişi
- Kişiler sırayla konuşmalı
- Mümkün olduğunca sessiz ortam
- Bilinçli overlap (aynı anda konuşma) olmamalı
- Format: WAV, 16 kHz veya üzeri; mono ya da stereo olabilir

Bu ses dosyası `.gitignore` nedeniyle GitHub'a **commit edilmez**. Her geliştirici kaydı kendi makinesinde `tests/data/` klasörüne koyar.

**Sonraki kalite testleri için not:** Milestone kalite testleri için henüz hazırlanması gereken üç kayıt daha vardır:

- `three_speakers.wav`
- `short_utterances.wav`
- `overlap.wav`

Bu kayıtların senaryoları `tests/data/README.md` içinde açıklanmıştır.

## 7. Backend'i Başlatma

Varsayılan `auto` cihaz seçimiyle sunucuyu başlatın:

```powershell
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

- Sunucu yalnızca yerel makinede çalışır; kimlik doğrulama yoktur. `127.0.0.1` dışında dinletmeyin.
- Adres: `http://127.0.0.1:8000`
- Modeller açılışta yüklendiği için ilk açılış biraz sürebilir. İlk çalıştırmada Whisper Turbo ağırlıkları (yaklaşık 1.5 GB) `%USERPROFILE%\.cache\whisper` klasörüne indirildiği için daha uzun sürer.
- Terminalde `Application startup complete.` satırı göründüğünde sunucu hazırdır.
- CUDA mevcutsa `auto` GPU'yu seçer; CUDA yoksa CPU seçilir.
- Sunucu çalıştığı sürece bu terminal meşgul kalır. `curl.exe` komutları için ikinci bir terminal açın.

## 8. Health Kontrolü

Tarayıcıdan şu adrese gidin:

```text
http://127.0.0.1:8000/health
```

Ya da Windows PowerShell 5.1'de:

```powershell
curl.exe http://127.0.0.1:8000/health
```

GPU için beklenen örnek yanıt:

```json
{"status":"ok","device":"cuda"}
```

CPU için beklenen örnek yanıt:

```json
{"status":"ok","device":"cpu"}
```

## 9. Swagger Üzerinden Manuel Test

Ana manuel test yöntemi FastAPI'nin Swagger arayüzüdür. Tarayıcıdan şu adrese gidin:

```text
http://127.0.0.1:8000/docs
```

1. `POST /diarize` endpoint'ini açın.
2. `Try it out` düğmesini seçin.
3. `file` alanındaki dosya seçme düğmesiyle `tests/data/two_speakers_clean.wav` dosyasını seçin.
4. `Execute` düğmesine basın.
5. İşlemin bitmesini bekleyin. 55 sn'lik bir kayıt GPU'da yaklaşık 10 sn, CPU'da yaklaşık 1 dakika sürer. Ardından "Server response" bölümünde HTTP `200` yanıtını ve "Response body" içindeki JSON'u kontrol edin.

İsteğe bağlı olarak aynı istek komut satırından da gönderilebilir:

```powershell
curl.exe -F "file=@tests/data/two_speakers_clean.wav" http://127.0.0.1:8000/diarize
```

## 10. Beklenen JSON Çıktısı

Yanıtta en az şu alanlar bulunur:

- `source_file`: yüklenen dosyanın adı
- `speaker_count`: tespit edilen farklı konuşmacı sayısı
- `segments`: konuşmacı segmentleri
- `output_file`: `outputs/` altına kaydedilen dosyanın adı

Her segmentte şu alanlar bulunur:

- `speaker`: anonim konuşmacı etiketi
- `start`: başlangıç zamanı, saniye cinsinden
- `end`: bitiş zamanı, saniye cinsinden
- `text`: bu aralıkta söylenen metin

**Aşağıdaki içerik yalnızca temsili bir örnektir; gerçek çıktı kayda göre değişir:**

```json
{
  "source_file": "two_speakers_clean.wav",
  "speaker_count": 2,
  "segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.84,
      "end": 7.34,
      "text": "Örnek konuşma metni."
    },
    {
      "speaker": "SPEAKER_01",
      "start": 7.83,
      "end": 12.70,
      "text": "İkinci konuşmacının örnek metni."
    }
  ],
  "output_file": "ornek_sonuc.json"
}
```

Diğer notlar:
- Segmentler başlangıç zamanına göre sıralıdır.
- Farklı konuşmacılara ait segmentler zaman olarak çakışabilir.
- Gerçek `output_file` adı `<tarih-saat>_<dosya_adı>.json` biçimindedir.

## 11. outputs/ Klasörünü Kontrol Etme

Başarılı her işlemden sonra `outputs/` klasöründe, yanıttaki `output_file` adıyla bir JSON dosyası oluşur.

PowerShell'de dosyaları listelemek ve içeriği Türkçe karakterler bozulmadan görüntülemek için:

```powershell
Get-ChildItem outputs
Get-Content -Encoding UTF8 outputs\<output_file_değeri>
```

Kontrol listesi:

- [ ] JSON dosyası oluşmuş mu?
- [ ] Dosya açılabiliyor mu?
- [ ] `source_file` doğru mu?
- [ ] `speaker_count` doğru mu?
- [ ] `segments` mevcut mu?
- [ ] Her segmentte `speaker`, `start`, `end` ve `text` alanları var mı?
- [ ] API yanıtındaki transkript ile dosyanın içeriği aynı mı? (Dosyada yalnızca `output_file` alanı bulunmaz.)

`outputs/*.json` dosyaları Git'e **commit edilmez**.

## 12. Manuel Kalite Kontrolü

Orijinal sesi dinleyip JSON çıktısıyla karşılaştırın ve şunları kontrol edin:

- [ ] Konuşmacı sayısı doğru mu?
- [ ] `SPEAKER_00` ve `SPEAKER_01` geçişleri yaklaşık doğru yerlerde mi?
- [ ] `text` alanları gerçekten konuşulanlara yakın mı?
- [ ] Konuşmacı değişim sınırında bazı kelimeler yanlış kişiye kaymış mı?
- [ ] Çok kısa segmentlerde `text: ""` bulunuyor mu?
- [ ] Aynı anda konuşma varsa çıktı nasıl davranmış?

**Mevcut bilinen baseline sınırlamaları:**

- Konuşmacı sınırlarında bazı kelimeler komşu konuşmacıya kayabilir. Mevcut iki konuşmacılı baseline testinde bunun örnekleri görülmüştür.
- Çok kısa veya çakışan diarization segmentlerinde `text: ""` olabilir.
- Overlap sırasında Whisper çoğunlukla baskın sesi daha iyi transcribe eder.
- Whisper bazı Türkçe kelimeleri hatalı tanıyabilir.
- Bunlar mevcut bilinen sınırlamalardır ve ileride ayrı kalite testleriyle geliştirilecektir.

**Mevcut baseline ölçümleri** (`two_speakers_clean.wav`; RTX 4070 Laptop GPU):

- Test kaydı: yaklaşık 55 saniye
- GPU işlem süresi: yaklaşık 10 saniye
- CPU işlem süresi: yaklaşık 61 saniye
- 2 konuşmacı doğru tespit edildi
- Whisper'ın ürettiği 110 kelimenin 110'u final çıktıda yer aldı

Bu değerler kullanılan donanıma ve ses kaydına göre değişebilir.

## 13. CPU Modunda Manuel Test

GPU'lu bir makinede CPU davranışını test etmek için önce çalışan sunucuyu `Ctrl + C` ile durdurun. Ardından aynı terminalde:

```powershell
$env:APP_DEVICE="cpu"
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

- `/health` kontrolünde `device` alanı `cpu` olmalıdır.
- Swagger testini (bölüm 9) aynı şekilde tekrarlayın.
- CPU modunun GPU'ya göre belirgin şekilde daha yavaş olması normaldir.

Test tamamlandıktan sonra sunucuyu durdurun ve ortam değişkenini temizleyin:

```powershell
Remove-Item Env:APP_DEVICE
```

## 14. Sunucuyu Durdurma

Sunucunun çalıştığı terminalde `Ctrl + C` tuşlarına basın.

## 15. Otomatik Testleri Çalıştırma

Birim / hızlı testler (model, token veya ses kaydı gerektirmez):

```powershell
uv run pytest -m "not integration"
```

Entegrasyon testleri (gerçek modelleri kullanır; Hugging Face erişimi ve `tests/data/` kayıtları gerekir, birkaç dakika sürebilir):

```powershell
uv run pytest -m integration
```

Mevcut doğrulanmış durum:

- Birim testleri: 36/36 geçti.
- Entegrasyon testleri: 5 geçti.
- 9 entegrasyon testi, eksik yerel kayıtlar (`three_speakers.wav`, `short_utterances.wav`, `overlap.wav`) nedeniyle skip edildi.

Skip durumu bir hata değildir. Bir kayıt `tests/data/` altında yoksa ona bağlı testler bilinçli olarak atlanır. Kayıtlar eklendiğinde bu testler çalışır.

## 16. İsteğe Bağlı Diarization CLI Testi

Ana kullanım ve manuel test yolu FastAPI + Swagger'dır. Yalnızca diarization modülünü denemek için CLI da kullanılabilir. CLI yalnızca konuşmacı ve zaman bilgisini döndürür; `text` alanı içermez ve `outputs/` altına dosya yazmaz.

```powershell
uv run python -m diarization tests/data/two_speakers_clean.wav --device auto
```

JSON çıktı stdout'a, kullanılan cihaz stderr'e yazılır. `--device` değeri `auto`, `cpu` veya `cuda` olabilir.

## 17. Bilinen Sınırlamalar

- Konuşmacı sınırlarında kelime kayması olabilir.
- Çok kısa segmentlerde boş `text` olabilir.
- Overlapping speech kusursuz ayrılmaz.
- Whisper bazı Türkçe kelimeleri yanlış tanıyabilir.
- Uzun kayıtlar özellikle CPU'da yavaş olabilir.
- Sistem şu anda yerel ve tek kullanıcı odaklıdır.

## 18. Lisans / Atıf

- Bu lisans notu projenin kendi lisansı değildir.
- Projede kullanılan üçüncü taraf `pyannote/speaker-diarization-community-1` modeli CC-BY-4.0 lisansı altındadır ve uygun atıf gerektirir.
- Projenin kendi lisansı henüz belirlenmemiştir.

## 19. Geliştirme Yöntemi

Proje bağlamı şu dosyalarla korunur:

- `CLAUDE.md`
- `PROJECT_BRAIN.md`
- `CURRENT_STATE.md`
- `DECISIONS.md`

Geliştirme şu sırayı izler:

```text
Plan → Uygula → Test → Doğrula → Commit
```
