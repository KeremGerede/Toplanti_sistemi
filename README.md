# Toplantı Asistanı

Zamanla fiziksel bir ses yakalama cihazını bilgisayar tarafındaki AI işlemeyle birleştirecek bir toplantı sesi projesi.

Bu README, projeyi ilk kez açan birinin kurulumdan manuel teste kadar her adımı sırayla uygulayabileceği bir rehberdir. Komutlar Windows PowerShell 5.1 ile uyumludur.

## Hızlı Başlangıç (kurulum daha önce yapıldıysa)

İki ayrı terminal açın; ikisi de **proje kökünde** (`Toplanti_sistemi` klasörü) başlasın.

**Terminal 1 — backend:**

```powershell
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend:**

```powershell
cd frontend
npm run dev
```

Sonra tarayıcıda **http://localhost:5173** adresini açın.

İlk kurulum için bölüm 4 ve 5'e, ayrıntılı çalıştırma için bölüm 6'ya bakın.

## 1. Proje Özeti

Mevcut akış:

```text
Ses dosyası (WAV/FLAC)
  → speaker diarization (pyannote Community-1)
  → Speech-to-Text (Whisper Turbo, Türkçe)
  → konuşmacı / metin eşleştirme (alignment)
  → FastAPI backend (POST /diarize)
  → React + Vite frontend
  → JSON çıktı
```

- Konuşmacılar gerçek isimlerle değil, `SPEAKER_00`, `SPEAKER_01`, `SPEAKER_02` gibi anonim etiketlerle gösterilir. Etiketler, konuşmacıların kayıtta ilk konuşma sırasına göre verilir.
- **Gerçek kişi tanıma yapılmaz.** Sistem "kim ne zaman konuştu" sorusunu anonim etiketlerle yanıtlar; konuşmacının kim olduğunu bilmez.

Ayrıntılı durum ve ölçümler için `CURRENT_STATE.md`, alınan kararlar için `DECISIONS.md` dosyasına bakın.

## 2. Mevcut Özellikler

- Speaker diarization (`pyannote/speaker-diarization-community-1`)
- Türkçe Speech-to-Text (Whisper Turbo)
- CPU / CUDA otomatik cihaz seçimi
- Konuşmacı + zaman + metin içeren JSON çıktısı
- Yerel FastAPI backend ve Swagger arayüzü (`/docs`)
- **Frontend V0** (React + Vite): dosya seçme, analiz başlatma, transkript görüntüleme
- `outputs/` klasörüne JSON sonuç kaydı
- Yüklenen orijinal ses dosyası işlem sonrası silinir, kalıcı olarak saklanmaz
- Geliştiriciler için kalite ölçüm aracı (`quality/`; bkz. bölüm 15)

Henüz olmayan özellikler için bölüm 18'e bakın.

## 3. Gereksinimler

- **Python** 3.10 veya üzeri (3.13 ile doğrulandı)
- **`uv`** paket yöneticisi: https://docs.astral.sh/uv/ (Windows'ta `winget install astral-sh.uv` ile kurulabilir)
- **Node.js + npm**: Node.js 20.19+ veya 22.12+ (Vite'ın gereksinimi; v26.7 ile doğrulandı). npm, Node.js ile birlikte gelir.
- **Git**
- **Hugging Face hesabı**
- **`pyannote/speaker-diarization-community-1` model erişimi** (bkz. bölüm 5)
- **İnternet bağlantısı:** ilk kurulum ve ilk çalıştırmadaki model indirmeleri için
- **Disk alanı:** birkaç GB (CUDA'lı PyTorch ve Whisper Turbo modeli için)
- **NVIDIA GPU (isteğe bağlı, zorunlu değil):**
  - CUDA varsa GPU kullanılır ve işlem çok daha hızlıdır. CUDA Toolkit kurmak gerekmez; güncel bir NVIDIA sürücüsü yeterlidir.
  - GPU yoksa proje CPU ile çalışır, yalnızca daha yavaştır.

## 4. İlk Kurulum

### 4.1 Repoyu klonlama

```powershell
git clone https://github.com/KeremGerede/Toplanti_sistemi.git
cd Toplanti_sistemi
```

Not: Güncel geliştirme şu an `milestone-1-diarization` dalındadır ve henüz `main`'e alınmamıştır. Bu dalla çalışmak için:

```powershell
git checkout milestone-1-diarization
```

**Bundan sonraki bütün komutlar, aksi belirtilmedikçe proje kökünde (`Toplanti_sistemi` klasörü) çalıştırılır.**

### 4.2 Backend bağımlılıkları

```powershell
uv sync
```

Windows ve Linux'ta PyTorch'un CUDA 12.8 build'i kurulur. Bu build GPU olmayan makinede de CPU ile çalışır.

CUDA kontrolü:

```powershell
uv run python -c "import torch; print(torch.cuda.is_available())"
```

- `True` → CUDA kullanılabilir; sistem GPU ile çalışır.
- `False` → sistem CPU ile çalışabilir.

### 4.3 Frontend bağımlılıkları

```powershell
cd frontend
npm install
cd ..
```

Son satırdaki `cd ..` ile proje köküne geri dönülür. Sonraki komutlar yine proje kökünde çalışır.

## 5. Hugging Face Kurulumu

Diarization modeli (Community-1) gated'dir; kullanmadan önce erişim izni gerekir.

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

- kaynak koda
- README'ye
- GitHub reposuna
- commit geçmişine

### Model indirme notları

- Diarization modeli ilk kullanımda Hugging Face cache'ine iner. Sonraki çalıştırmalar `HF_HUB_OFFLINE=1` ile çevrimdışı yapılabilir.
- Windows'taki Hugging Face "symlink" uyarısı zararsızdır; `HF_HUB_DISABLE_SYMLINKS_WARNING=1` ile susturulabilir.

## 6. Projeyi Ayağa Kaldırma (Adım Adım)

Projeyi çalıştırmak için **iki ayrı terminal** gerekir: biri backend, biri frontend için. İki terminal de **proje kökünde** açılır. Önce backend başlatılır.

### Terminal 1 — Backend

```powershell
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

- Adres: `http://127.0.0.1:8000`
- Modeller açılışta yüklendiği için ilk açılış biraz sürer. Terminalde `Application startup complete.` satırı göründüğünde backend hazırdır.
- İlk çalıştırmada Whisper Turbo ağırlıkları (yaklaşık 1.5 GB) `%USERPROFILE%\.cache\whisper` klasörüne indirildiği için açılış daha uzun sürer.
- CUDA mevcutsa GPU, yoksa CPU otomatik seçilir.
- Backend yalnızca yerel makinede çalışır; kimlik doğrulama yoktur. `127.0.0.1` dışında dinletmeyin.
- Backend çalıştığı sürece bu terminal meşgul kalır.
- Analiz sırasında bu terminalde `Failed to launch Triton kernels … falling back …` uyarısı görülebilir. Windows'ta zararsızdır; Whisper daha yavaş ama doğru bir yönteme geçer.

**Health kontrolü.** Tarayıcıdan `http://127.0.0.1:8000/health` adresine gidin ya da ayrı bir PowerShell penceresinde şunu çalıştırın:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Beklenen yanıt GPU için:

```json
{"status":"ok","device":"cuda"}
```

CPU için:

```json
{"status":"ok","device":"cpu"}
```

**Swagger arayüzü:** `http://127.0.0.1:8000/docs`

### Terminal 2 — Frontend

Proje kökünden:

```powershell
cd frontend
npm run dev
```

- Terminalde `Local: http://localhost:5173/` satırı görünür.
- Tarayıcıda **http://localhost:5173** adresini açın.
- Vite geliştirme proxy'si, frontend'in `/diarize` ve `/health` isteklerini yerel FastAPI backend'e (`http://127.0.0.1:8000`) yönlendirir. Bu yüzden CORS ayarı yapmaya gerek yoktur.
- Backend çalışmıyorsa frontend analiz sırasında "Backend'e ulaşılamadı." mesajı gösterir. Backend hazır olmadan istek atılırsa frontend terminalinde `http proxy error … ECONNREFUSED` satırları görülür; backend hazır olunca kaybolur.
- Bu terminal `frontend` klasöründe kalır. Frontend'i durdurduktan sonra proje köküne `cd ..` ile dönülür.

## 7. Frontend'den Manuel Test (ana kullanım yolu)

1. Backend'i başlatın (bölüm 6, Terminal 1).
2. Frontend'i başlatın (bölüm 6, Terminal 2).
3. Tarayıcıdan `http://localhost:5173` adresini açın.
4. Dosya seçme düğmesinden bir WAV veya FLAC dosyası seçin. Düğmenin adı tarayıcı diline göre `Dosya Seç` ya da `Choose File` olabilir.
5. **Analiz Et** düğmesine basın.
6. Düğmede `Analiz ediliyor...` yazısı görünür; işlemin bitmesini bekleyin. 55 sn'lik bir kayıt GPU'da yaklaşık 10 sn, CPU'da yaklaşık 1 dakika sürer.
7. Sonuç geldiğinde şunları inceleyin:
   - dosya adı
   - konuşmacı sayısı
   - konuşmacı segmentleri (`SPEAKER_00`, `SPEAKER_01`, …)
   - her segmentin başlangıç / bitiş zamanı (`mm:ss.mmm`)
   - transkript metni

Diğer davranışlar:
- Metni olmayan (boş) segmentler silinmez; frontend'de `(metin yok)` olarak gösterilir.
- Hata olursa (ör. ses olmayan bir dosya) ekranda backend'in hata mesajı gösterilir.

**Yerel test kaydı:** `tests/data/three_speakers.wav` kullanılabilir. Test kayıtları Git'e commit edilmez; her geliştiricinin kendi makinesinde bulunur (bkz. bölüm 11).

> **Önemli:** Bu kayıtta 3 gerçek konuşmacı olmasına rağmen mevcut sistem **2 konuşmacı** bulur. Bu bir frontend hatası değildir; mevcut diarization baseline'ının sonucudur (bkz. bölüm 16).

## 8. Frontend Olmadan API Testi (Swagger, geliştirici / debug)

Ana kullanıcı yolu Frontend V0'dır. Swagger, geliştirme ve hata ayıklama için kullanılır.

1. Backend çalışırken `http://127.0.0.1:8000/docs` adresini açın.
2. `POST /diarize` endpoint'ini açın.
3. `Try it out` düğmesini seçin.
4. `file` alanından bir WAV veya FLAC dosyası seçin.
5. `Execute` düğmesine basın.
6. "Server response" bölümünde HTTP `200` yanıtını ve "Response body" içindeki JSON'u kontrol edin.

Aynı istek komut satırından da gönderilebilir:

```powershell
curl.exe -F "file=@tests/data/three_speakers.wav" http://127.0.0.1:8000/diarize
```

## 9. API Yanıtı (JSON)

`POST /diarize` yanıtında şu alanlar bulunur:

- `source_file`: yüklenen dosyanın adı
- `speaker_count`: tespit edilen farklı konuşmacı sayısı
- `segments`: konuşmacı segmentleri
- `output_file`: `outputs/` altına kaydedilen dosyanın adı (frontend bu alanı kullanmaz)

Her segmentte şu alanlar bulunur:

- `speaker`: anonim konuşmacı etiketi
- `start`: başlangıç zamanı, saniye cinsinden
- `end`: bitiş zamanı, saniye cinsinden
- `text`: bu aralıkta söylenen metin

**Aşağıdaki içerik yalnızca temsili bir örnektir; gerçek çıktı kayda göre değişir:**

```json
{
  "source_file": "three_speakers.wav",
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

## 10. outputs/ Klasörü

Başarılı her analizden sonra (frontend veya Swagger fark etmez) transkript JSON'u `outputs/` klasörüne, yanıttaki `output_file` adıyla yazılır. Dosyanın içeriği, API yanıtının `output_file` alanı dışındaki kısmıyla aynıdır.

PowerShell'de dosyaları listelemek ve içeriği Türkçe karakterler bozulmadan görüntülemek için:

```powershell
Get-ChildItem outputs
Get-Content -Encoding UTF8 outputs\<output_file_değeri>
```

`outputs/*.json` dosyaları Git'e **commit edilmez**.

Veritabanı (SQLite) henüz yok. Bu yüzden şunlar **mevcut değil**:
- analiz geçmişi
- geçmiş kayıt ekranı
- JSON İndir düğmesi

Sonuçlara şu an yalnızca `outputs/` klasöründen ulaşılır.

## 11. Test Kayıtları

Test kayıtları `tests/data/` altında durur. Gizlilik ve repo boyutu nedeniyle ses dosyaları ve referans (ground truth) dosyaları Git'e **commit edilmez**. Her geliştirici kayıtları kendi makinesinde bu klasöre koyar.

| Kayıt | Durum |
|---|---|
| `two_speakers_clean.wav` | Yerelde mevcut; 2 konuşmacı. Referansı henüz hazırlanmadı. |
| `three_speakers.wav` | Yerelde mevcut; 3 konuşmacı. Referansı (`three_speakers.reference.json`) hazır. |
| `short_utterances.wav` | Henüz hazırlanmadı |
| `overlap.wav` | Henüz hazırlanmadı |

Kayıt senaryoları ve referans formatı `tests/data/README.md` içinde açıklanmıştır. Önerilen format: WAV, 16 kHz veya üzeri; mono ya da stereo olabilir.

## 12. Frontend Build (isteğe bağlı doğrulama)

```powershell
cd frontend
npm run build
cd ..
```

Build çıktısı `frontend/dist/` altında oluşur ve Git'e commit edilmez. Günlük kullanım için build gerekmez; `npm run dev` yeterlidir.

## 13. CPU Modunda Çalıştırma

GPU'lu bir makinede CPU davranışını test etmek için önce çalışan backend'i `Ctrl + C` ile durdurun. Ardından aynı terminalde (proje kökünde):

```powershell
$env:APP_DEVICE="cpu"
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

- `/health` kontrolünde `device` alanı `cpu` olmalıdır.
- Frontend aynen kullanılabilir.
- CPU modunun GPU'ya göre belirgin şekilde daha yavaş olması normaldir.

Test tamamlandıktan sonra backend'i durdurun ve ortam değişkenini temizleyin:

```powershell
Remove-Item Env:APP_DEVICE
```

## 14. Sunucuları Durdurma

- Backend terminalinde: `Ctrl + C`
- Frontend terminalinde: `Ctrl + C`

## 15. Otomatik Testler

Birim / hızlı testler (model, token veya ses kaydı gerektirmez):

```powershell
uv run pytest -m "not integration"
```

Entegrasyon testleri (gerçek modelleri kullanır; Hugging Face erişimi ve `tests/data/` kayıtları gerekir, birkaç dakika sürer):

```powershell
uv run pytest -m integration
```

**Son doğrulanmış durum (2026-09-24):**

- Birim testleri: **56/56 geçti** (kalite metrikleri testleri dahil).
- Entegrasyon testleri: **6 geçti, 2 başarısız, 6 skip.**
  - Başarısız olan testler: `test_three_speakers[auto]` ve `test_three_speakers[cpu]`. Beklenen 3 konuşmacı yerine 2 konuşmacı bulunuyor. Bu, bilinen diarization sorunudur (bölüm 16); test hatası değildir.
  - Skip edilen testler: `short_utterances.wav` ve `overlap.wav` henüz olmadığı için bunlara bağlı 6 test. Skip bir hata değildir; kayıtlar eklendiğinde bu testler çalışır.

**Kalite ölçüm aracı (geliştirici):** Bir kaydın referansı hazırsa mevcut sistemin kalitesi şöyle ölçülür:

```powershell
uv run python -m quality.benchmark tests/data/three_speakers.wav --reference tests/data/three_speakers.reference.json
```

Raporlar `tests/data/results/` altına yazılır ve commit edilmez. Ayrıntılar `tests/data/README.md` içinde.

## 16. Bilinen Mevcut Kalite Durumu

**`two_speakers_clean.wav`** (~55 sn, 2 konuşmacı):
- 2 konuşmacı doğru bulunuyor.
- İşlem süresi GPU'da ~10 sn, CPU'da ~61 sn.
- Konuşmacı sınırlarında bazı kelimelerin komşu konuşmacıya kaydığı gözlendi.
- Referansı henüz hazırlanmadığı için sayısal kalite ölçümü yok.

**`three_speakers.wav`** (~53 sn, temiz 3 konuşmacı). Değerler bağımsız bir insan referansına göre ölçüldü:

| Ölçüm | Sonuç |
|---|---|
| Gerçek konuşmacı sayısı | 3 |
| Community-1 otomatik sonucu | **2 konuşmacı** (A ve B aynı kümede, C ayrı) |
| DER | ~%41.1 |
| Konuşmacı karışması (confusion) | ~%29.5 |
| Whisper Turbo STT WER | ~%1.4 |
| Oracle diarization ile alignment | Kayan kelime 0 |
| Ana darboğaz | **Diarization** |

**`num_speakers=3` teşhisi** (yalnızca deney; üründe konuşmacı sayısı verilmez):
- 3 küme üretiyor, ancak A ve B doğru ayrılmıyor; kümeler konuşmacıya değil zamana göre bölünüyor.
- DER ~%43.3 (daha kötü).
- Sonuç: Sorun yalnızca konuşmacı sayısının tahmin edilmesi değil.

**Speaker embedding teşhisi:**
- Referans turlardan çıkarılan Community-1 embedding'leri A ile B'yi belirgin biçimde ayırabiliyor.
  - Aynı konuşmacı benzerliği (A-A / B-B): yaklaşık 0.60–0.65.
  - Farklı konuşmacı benzerliği (A-B): yaklaşık 0.16–0.19.
  - Zaman kaynaklı bir kayma gözlenmedi.
- **Mevcut güçlü hipotez** (henüz kanıtlanmadı): Sorun embedding modelinin kişileri ayırt edememesi değil. Pipeline'ın kayan pencere (sliding-window), segmentasyon maskesi ve embedding çıkarma aşamasında olabilir.

Bu değerler kullanılan donanıma ve ses kaydına göre değişebilir.

## 17. Sıradaki Teknik Adım

Bir sonraki kalite teşhisi: Community-1 pipeline'ının clustering'e gerçekten verdiği pencere bazlı (sliding-window) embedding'lerin incelenmesi.

Bulguya göre şunlardan biri değerlendirilecek:
- clustering ayarları
- alternatif bir diarization yaklaşımı

## 18. Frontend V0 Sınırları

Frontend şu an yalnızca şunları yapar:

- dosya seçme (WAV / FLAC)
- analiz başlatma
- yükleme durumu (`Analiz ediliyor...`)
- hata mesajı gösterme
- transkript görüntüleme

**Henüz olmayanlar:**

- SQLite / veritabanı
- analiz geçmişi ve geçmiş kaydı görüntüleme
- JSON İndir düğmesi
- login / kullanıcı sistemi
- audio player
- waveform
- transkript editörü
- canlı mikrofon
- gerçek zamanlı streaming

## 19. Bilinen Sınırlamalar

- Benzer sesli konuşmacılar aynı konuşmacıda birleşebilir (bkz. bölüm 16).
- Konuşmacı sınırlarında kelime kayması olabilir.
- Çok kısa segmentlerde boş `text` olabilir.
- Overlapping speech kusursuz ayrılmaz; aynı anda konuşmada Whisper çoğunlukla baskın sesi yazar.
- Whisper bazı Türkçe kelimeleri yanlış tanıyabilir.
- Uzun kayıtlar özellikle CPU'da yavaş olabilir.
- Sistem şu anda yerel ve tek kullanıcı odaklıdır.

## 20. İsteğe Bağlı Diarization CLI Testi

Yalnızca diarization modülünü denemek için CLI da kullanılabilir. CLI yalnızca konuşmacı ve zaman bilgisini döndürür; `text` alanı içermez ve `outputs/` altına dosya yazmaz.

```powershell
uv run python -m diarization tests/data/three_speakers.wav --device auto
```

JSON çıktı stdout'a, kullanılan cihaz stderr'e yazılır. `--device` değeri `auto`, `cpu` veya `cuda` olabilir.

## 21. Lisans / Atıf

- Bu lisans notu projenin kendi lisansı değildir.
- Projede kullanılan üçüncü taraf `pyannote/speaker-diarization-community-1` modeli CC-BY-4.0 lisansı altındadır ve uygun atıf gerektirir.
- Projenin kendi lisansı henüz belirlenmemiştir.

## 22. Geliştirme Yöntemi

Proje bağlamı şu dosyalarla korunur:

- `CLAUDE.md`
- `PROJECT_BRAIN.md`
- `CURRENT_STATE.md`
- `DECISIONS.md`
- `README.md`

Geliştirme şu sırayı izler:

```text
Plan → Onay → Uygula → Test → Doğrula → Dokümanları güncelle → Kullanıcı onayıyla commit
```
