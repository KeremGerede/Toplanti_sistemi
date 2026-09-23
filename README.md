# Toplantı Asistanı

Zamanla fiziksel bir ses yakalama cihazını bilgisayar tarafındaki AI işlemeyle birleştirecek bir toplantı sesi projesi.

## Mevcut Durum

Proje ilk geliştirme milestone'unda: kayıtlı sesten speaker diarization.

Bir toplantı kaydı verildiğinde modül, her zaman aralığında hangi anonim konuşmacının konuştuğunu belirler.

Örnek:

```text
00:00 - 00:04 → SPEAKER_00
00:04 - 00:09 → SPEAKER_01
00:09 - 00:13 → SPEAKER_00
```

Kullanıcı onayıyla bunun üzerine konuşmacılı transkript eklendi: yerel API, her konuşmacı segmentinde söylenen metni de döndürür. Ayrıntılı durum ve ölçümler için `CURRENT_STATE.md` dosyasına bakın.

## Mevcut Kapsam

- Kayıtlı sesi girdi olarak alır (WAV/FLAC).
- Speaker diarization çalıştırır; anonim konuşmacı etiketleri ve başlangıç/bitiş zamanlarını döndürür.
- Sonuçları JSON uyumlu veriye normalize eder.
- CUDA mevcutsa otomatik olarak kullanır, aksi halde CPU'ya geri döner.
- Whisper ile Türkçe transkripsiyon yapar ve kelimeleri konuşmacı segmentleriyle eşler.
- Yerel FastAPI backend ile sonucu döndürür ve `outputs/` klasörüne kaydeder.

## Teknoloji

- Python 3.13, `uv`
- PyTorch (Windows/Linux'ta CUDA 12.8 build'i)
- pyannote.audio + `speaker-diarization-community-1`
- openai-whisper (`turbo`)
- FastAPI + uvicorn

## Kurulum

```bash
uv sync
```

**Hugging Face erişimi** (diarization modeli gated):

1. https://huggingface.co/pyannote/speaker-diarization-community-1 sayfasında kullanım koşullarını kabul edin.
2. https://hf.co/settings/tokens adresinden **read** yetkili bir token oluşturun.
3. Giriş yapın:

   ```bash
   uv run hf auth login
   ```

   Token gizli bir girişle istenir ve repo dışında saklanır. Alternatif olarak Windows "Ortam Değişkenleri" penceresinden kullanıcı düzeyinde `HF_TOKEN` tanımlanabilir.

**Token'ı asla koda, MD dosyalarına veya repoya yazmayın.**

**İlk çalıştırmada modeller iner:**
- Diarization modeli Hugging Face cache'ine iner.
- Whisper `turbo` ağırlıkları (yaklaşık 1.5 GB) `%USERPROFILE%\.cache\whisper` klasörüne iner.
- Sonraki çalıştırmalar çevrimdışı yapılabilir (`HF_HUB_OFFLINE=1`).
- Windows'taki HF symlink uyarısı zararsızdır; `HF_HUB_DISABLE_SYMLINKS_WARNING=1` ile susturulabilir.

## Kullanım

### Diarization CLI

Yalnızca konuşmacı ve zaman bilgisini, metin olmadan döndürür:

```bash
uv run python -m diarization toplanti.wav --device auto
```

JSON çıktı stdout'a, kullanılan cihaz stderr'e yazılır. `--device` değeri `auto`, `cpu` veya `cuda` olabilir.

### Yerel API (konuşmacılı transkript)

```bash
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Sunucuyu yalnızca `127.0.0.1` üzerinde çalıştırın; kimlik doğrulama yoktur. Cihaz seçimi `APP_DEVICE` ortam değişkeniyle yapılır: `auto` (varsayılan), `cpu` veya `cuda`.

Sağlık kontrolü:

```bash
curl.exe http://127.0.0.1:8000/health
```

Transkript isteği:

```bash
curl.exe -F "file=@toplanti.wav" http://127.0.0.1:8000/diarize
```

Yanıt aşağıdaki nesneye ek olarak kaydedilen dosyanın adını (`output_file`) içerir. Sonuç `outputs/<zaman>_<dosya_adı>.json` olarak kaydedilir:

```json
{
  "source_file": "toplanti.wav",
  "speaker_count": 2,
  "segments": [
    {"speaker": "SPEAKER_00", "start": 0.841, "end": 7.338, "text": "..."}
  ]
}
```

Yüklenen ses işlendikten sonra silinir. `outputs/` içeriği commit edilmez.

## Testler

```bash
uv run pytest -m "not integration"
```

```bash
uv run pytest -m integration -rP
```

- Birim testleri model gerektirmez.
- Entegrasyon testleri gerçek modelleri kullanır; HF erişimi ve `tests/data/` altındaki kayıtlar gerekir. Beklenen kayıtlar `tests/data/README.md` içinde açıklanmıştır. Eksik kayıtlar için testler skip edilir.

## Henüz Implemente Edilmeyenler

- Gerçek zamanlı streaming
- UI
- Minimal yerel `POST /diarize` dışındaki API özellikleri
- Veritabanı
- Cihaz iletişimi
- Konuşmacı kimliği tanıma
- Toplantı özetleri
- LLM özellikleri

## Lisans Notu

Bu not projenin kendi lisansı değildir. Projede kullanılan üçüncü taraf `pyannote/speaker-diarization-community-1` modeli CC-BY-4.0 lisanslıdır ve kullanımında atıf gerekir. Projenin kendi lisansı henüz belirlenmemiştir.

## Geliştirme Yöntemi

Proje bağlamı şu dosyalarla korunur:

- `CLAUDE.md`
- `PROJECT_BRAIN.md`
- `CURRENT_STATE.md`
- `DECISIONS.md`

Geliştirme şu sırayı izler:

```text
Plan → Uygula → Test → Doğrula → Commit
```
