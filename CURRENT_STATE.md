# CURRENT_STATE.md

## Mevcut Aşama
Milestone-1 (speaker diarization modülü) implemente edildi; 3 test kaydının baseline'ı bekleniyor.
Kullanıcı onaylı kapsam genişlemesi olarak konuşmacılı transkript (Whisper) ve yerel FastAPI backend eklendi.

## Mevcut Milestone
İlk bağımsız speaker diarization modülünü geliştirmek ve doğrulamak.

## Onaylanmış Gereksinimler
- Girdi başlangıçta kayıtlı bir ses dosyası olacak.
- Çıktı konuşmacıları `SPEAKER_00`, `SPEAKER_01` vb. olarak tanımlayacak.
- Gerçek kimlikler gerekli değil.
- Modül konuşmacı segmentlerinin başlangıç/bitiş zaman damgalarını döndürmeli.
- Çıktı JSON uyumlu olmalı.
- Varsayılan hesaplama modu otomatik olmalı.
- CUDA GPU mevcutsa kullanılmalı.
- Fallback olarak CPU kullanılmalı.
- İlk diarization yığını: `pyannote.audio` + `speaker-diarization-community-1`.
- Mimari, ileride canlı ses desteğini engellememeli.
- (Kapsam genişlemesi) Yerel API çıktısında her segment için söylenen metin (`text`) de yer almalı.

## Tamamlananlar
- Python ortamı (`uv`, Python 3.13) ve bağımlılıklar. Windows'ta CUDA'lı torch, PyTorch cu128 index'inden geliyor.
- `diarization/` modülü:
  - `auto`/`cpu`/`cuda` cihaz seçimi.
  - soundfile ile bellekten ses okuma (FFmpeg gerekmez).
  - Sonuç normalizasyonu.
  - CLI: `python -m diarization`.
- `transcription/` modülü:
  - Whisper `turbo` ile kelime zaman damgalı Türkçe transkripsiyon.
  - Kelime → konuşmacı segmenti eşleme (0.5 sn tolerans).
- `api/` modülü: yerel FastAPI, `GET /health`, `POST /diarize`, çıktılar `outputs/` altına.
- Birim ve entegrasyon testleri.
- Test kaydı `two_speakers_clean.wav` ile uçtan uca doğrulama (GPU ve CPU).

## Bekleyenler
- Test kayıtları: `three_speakers.wav`, `short_utterances.wav`, `overlap.wav` (bkz. `tests/data/README.md`).
- Bu kayıtlarla entegrasyon testlerinin çalıştırılması:
  - 3 konuşmacı testi milestone-1'in zorunlu başarı kriteri.
  - Kısa konuşma ve overlap sonuçları baseline'a eklenecek.
- `POST /diarize` endpoint adının değerlendirilmesi (şimdilik korunuyor).

## Baseline (2026-09-23)

**Ortam:**

| Öğe | Değer |
|---|---|
| İşletim sistemi | Windows 11 |
| Python | 3.13.15 |
| torch | 2.11.0+cu128 |
| pyannote.audio | 4.0.7 |
| openai-whisper | 20250625 (`turbo`) |
| GPU | NVIDIA RTX 4070 Laptop, 8 GB |

**Test kaydı:** `two_speakers_clean.wav` (55.1 sn, 48 kHz, stereo, 2 konuşmacı)

| Ölçüm | Sonuç |
|---|---|
| Diarization | 2 konuşmacı, 20 segment. 1.5 sn'den kısa segment: 10. Farklı konuşmacılara ait çakışan segment çifti: 7. |
| Diarization GPU / CPU tutarlılığı | Çıktılar birebir aynı (zaman farkı 0.0 sn) |
| Whisper `turbo` | 110 kelime, algılanan dil `tr`. Kullanıcı kaliteyi bu aşama için yeterli buldu. Bazı yanlış tanımalar var (ör. "Ben sevirsin", "krafet katlamak"). |
| Konuşmacılı transkript | 20 segmentin 7'sinde `text` boş. 0.5 sn toleransı nedeniyle düşen kelime yok: 110 kelimenin 110'u çıktıda. |
| Konuşmacı sınırında kelime kayması | 2 yerde gözlendi. ~12.6 sn'deki "Ben" önceki konuşmacının (SPEAKER_00) segmentinde kalmış, cümlenin devamı SPEAKER_01'de. ~39.7 sn'deki "Başka" SPEAKER_01'de kalmış, devamı ("hakkında bir fikir geliyor mu?") SPEAKER_00'da. |
| Transkript metni GPU / CPU | 20 segmentin 15'inde metin aynı. Farklar noktalama ve bir kelime ("arada"). Segment zamanları ve etiketleri aynı. |

**Süreler:**

| İşlem | GPU (cuda) | CPU |
|---|---|---|
| Diarization (yalnız) | ~1.8–2.8 sn | ~20.6 sn |
| Whisper transkripsiyon (yalnız) | ~7.3 sn | — |
| `POST /diarize` uçtan uca | ~10.0 sn | ~61.4 sn |

**GPU bellek:**
- İki model birlikte yüklendiğinde yaklaşık 3.2 GB.
- İşlem sırasında kullanılan tepe değer yaklaşık 4.8 GB, ayrılmış (reserved) bellek yaklaşık 6.9 GB.

**Test sonuçları:**
- Birim testleri: 36/36 geçti.
  - Cihaz seçimi: 11
  - Normalizasyon: 8
  - Kelime eşleme: 11
  - API (sahte modellerle): 6
- Entegrasyon testleri: 5 geçti, 9 skip edildi.
  - Geçenler:
    - 2 konuşmacı testi (`auto` ve `cpu` ile)
    - GPU/CPU konuşmacı sayısı tutarlılığı
    - Transcriber
    - Gerçek modellerle API
  - Skip edilenler: 3 eksik kaydın her biri için 3 test.

## Bilinen Sınırlamalar
Bunlar şimdilik kabul edildi; düzeltmek için ek mantık eklenmeyecek.
- **Konuşmacı sınırında kelime kayması:** Whisper'ın kelime zamanları sapabildiği için sınırdaki kelimeler komşu konuşmacıya atanabilir.
- **Boş kısa segmentler:** Kısa diarization segmentleri (ör. 0.07 sn'lik parçalar) ve çakışma bölgeleri `text: ""` ile kalabilir.
- **Tolerans dışı kelimeler:** Hiçbir segmente 0.5 sn'den yakın olmayan kelimeler çıktıya girmez. Bu kayıtta böyle bir kelime olmadı.
- **Overlap:** Aynı anda konuşmada Whisper çoğunlukla baskın sesi yazar.
- **Süre ve bellek:**
  - İstekler senkron ve sırayla işleniyor. CPU'da uzun kayıtlar çok yavaş olabilir.
  - GPU'da ayrılmış bellek 8 GB'ın 6.9 GB'ı; çok uzun kayıtlarda bellek sınırı zorlanabilir.
  - Tüm ses belleğe okunuyor.
- **Güvenlik:** API'de kimlik doğrulama yok; yalnızca yerelde (`127.0.0.1`) çalıştırılmalı.

## Kapsam Dışı
- UI
- Minimal yerel `POST /diarize` dışındaki API özellikleri (kimlik doğrulama, ağa açma, kuyruk vb.)
- Veritabanı
- Ağ (networking)
- Fiziksel cihaz entegrasyonu
- Konuşmacı kimliği tanıma
- LLM özellikleri
- Canlı streaming implementasyonu

## Sonraki Adım
Kalan 3 test kaydını `tests/data/` klasörüne ekle, `uv run pytest -m integration -rP` ile entegrasyon testlerini çalıştır ve sonuçları bu dosyadaki baseline'a ekle.
