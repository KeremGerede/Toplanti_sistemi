# CURRENT_STATE.md

## Mevcut Aşama
V1.1 geliştirmesi sürüyor (tarih: 2026-09-24).

- Milestone-1 (speaker diarization modülü) implemente edildi. Ancak zorunlu kriter olan "temiz 3 konuşmacıda tam 3 konuşmacı" şu an **karşılanmıyor** (bkz. three_speakers baseline).
- Kullanıcı onaylı kapsam genişlemeleri: konuşmacılı transkript (Whisper), yerel FastAPI backend, Frontend V0.
- Kullanıcı onayıyla V1.1 sırası geçici olarak değişti:

  ```text
  baseline kalite ölçümü → Frontend V0 → diarization teşhisi / iyileştirme → SQLite + tam frontend özellikleri
  ```

- Diarization teşhisi tamamlandı (2026-09-24). Ana sorun Community-1'in segmentation / local speaker slot aşaması olarak tespit edildi. Slot-free kısa-pencere yaklaşımı güçlü bir çözüm adayı, ancak **henüz ürün koduna alınmadı** (bkz. "Diarization Teşhis Bulguları").
- Proje geçici olarak beklemeye alındı. Dönüşte ilk adım: `two_speakers_v2.reference.json` hazırlamak (bkz. "Sonraki Adım").

## Mevcut Milestone
- Milestone-1: İlk bağımsız speaker diarization modülünü geliştirmek ve doğrulamak. Açık kriter: 3 konuşmacı testi.
- V1.1 hedefleri:
  1. Transkript kalitesini ölçmek ve iyileştirmek.
  2. SQLite ile analiz geçmişi.
  3. Temel frontend (V0 tamamlandı).

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
- Varsayılan akışta konuşmacı sayısı verilmez (D-007).
- (Kapsam genişlemesi) Yerel API çıktısında her segment için söylenen metin (`text`) de yer almalı.
- (Kapsam genişlemesi, kullanıcı onaylı) Frontend V0: `POST /diarize` için ince bir görüntüleme katmanı.

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
- **C1 (`75b170a`):** CLAUDE.md'ye çalışma kuralı eklendi:
  - Planlamadan önce beş MD dosyası okunur.
  - Bir kararla çelişki varsa açıkça belirtilir ve kullanıcı onayı beklenir.
  - Commit öncesinde diff, status, token ve ignore kontrolü yapılır.
  - Commit ve push yalnızca kullanıcı onayıyla yapılır.
- **C2 (`a7788ca`):** Kalite ölçüm altyapısı:
  - `quality/metrics.py`: STT (WER, S/D/I), diarization (DER bileşenleri, konuşmacı sayısı, sınır sapması, kısa tur yakalama) ve alignment (oracle diarization, kayan kelime) metrikleri.
  - `quality/benchmark.py`: benchmark CLI.
  - 20 birim testi.
  - `tests/data/README.md`: ground truth formatı.
- **Ground truth:** `three_speakers.reference.json` kullanıcı tarafından sesi dinleyerek bağımsız hazırlandı (14 tur, A/B/C). Yerelde duruyor, commit edilmez.
- **Frontend V0 (`5340f36`):** React + Vite + JavaScript.
  - Çalışanlar: dosya seçme, `POST /diarize` ile analiz, yükleme durumu, transkript görüntüleme, boş metin için "(metin yok)", hata mesajları.
  - Vite dev proxy ile backend'e erişiyor; CORS eklenmedi.
  - Backend kodu değiştirilmedi.
- Uçtan uca doğrulama: `two_speakers_clean.wav` ve `three_speakers.wav` (GPU ve CPU; frontend üzerinden de).
- **Diarization teşhisi (2026-09-24):** gerçek pipeline embedding analizi, slot-free teşhisi, 2 konuşmacılı regresyon ve yeni bağımsız test kaydının doğrulanması. Hepsi yalnızca teşhis düzeyinde; ürün kodu değişmedi (bkz. "Diarization Teşhis Bulguları" 4–7).

## Bekleyenler
- **Diarization iyileştirmesi:** three_speakers'ta A ve B birleşiyor. Çözüm adayı (slot-free) teşhis düzeyinde; ürüne alınmadı (bkz. "Sonraki Adım").
- `two_speakers_v2.reference.json`: kullanıcı tarafından sesi dinleyerek bağımsız hazırlanacak (ilk adım).
- `two_speakers_clean.reference.json`: kullanıcı tarafından sıfırdan hazırlanacak (öncelik v2'den sonra).
- Test kayıtları: `short_utterances.wav` ve `overlap.wav` (bkz. `tests/data/README.md`).
- SQLite ile analiz geçmişi ve tam frontend özellikleri (V1.1'in sonraki aşaması).
- CLAUDE.md, PROJECT_BRAIN.md ve DECISIONS.md kapsam listelerinin Frontend V0 ve V1.1 durumuna göre güncellenmesi (hâlâ "UI" ve "Veritabanı" kapsam dışı yazıyor).
- `POST /diarize` endpoint adının değerlendirilmesi (şimdilik korunuyor).

## Baseline — two_speakers_clean (2026-09-23)

**Ortam:**

| Öğe | Değer |
|---|---|
| İşletim sistemi | Windows 11 |
| Python | 3.13.15 |
| torch | 2.11.0+cu128 |
| pyannote.audio | 4.0.7 |
| openai-whisper | 20250625 (`turbo`) |
| GPU | NVIDIA RTX 4070 Laptop, 8 GB |

**Test kaydı:** `two_speakers_clean.wav` (55.1 sn, 48 kHz, stereo, 2 konuşmacı). Referansı henüz yok; değerler gözlemdir.

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

## Baseline — three_speakers (2026-09-24)

**Test kaydı:** `three_speakers.wav` (52.6 sn, 48 kHz, stereo, temiz 3 konuşmacı; internet kaynaklı, yalnızca yerel test verisi). Bağımsız insan referansıyla ölçüldü (`quality.benchmark`).

| Ölçüm | Sonuç |
|---|---|
| Konuşmacı sayısı (gerçek / bulunan) | 3 / **2**. A ve B aynı kümede, C ayrı. |
| DER | ~%41.1 |
| Konuşmacı karışması | ~%29.5 |
| Kaçırılan konuşma | ~%11.5; büyük ölçüde tur kenarlarındaki zamanlama farkı. Kelime kaybı yok. |
| Yanlış alarm | ~%0.1 |
| Whisper Turbo WER | ~%1.4. Tek fark "Hımmm" → "Hmm"; gerçek tanıma hatası yok. Sayı yazımından kaynaklanan fark da yok. |
| Oracle diarization ile alignment | Kayan kelime 0, atanamayan kelime 0 |
| Gerçek diarization ile | 71 kelimenin 28'i yanlış konuşmacıda (B'nin kelimelerinin hepsi) |
| Süre (GPU) | Diarization 2.7 sn + STT 7.2 sn |
| GPU bellek tepesi | ~7.0 GB (`nvidia-smi`; ayrılmış bellek dahil) |

**Sonuç:** Bu kayıtta baskın sorun diarization; STT ve alignment bu kayıtta sorun değil.

## Diarization Teşhis Bulguları (2026-09-24)
Yalnızca teşhis amaçlı deneyler; ürün kodu ve ayarları değiştirilmedi.

**1. `num_speakers=3` teşhisi:**
- 3 küme çıkıyor, ancak A ve B konuşmacıya göre ayrılmıyor; kümeler zamana göre bölünüyor (0–12 sn ve 12–37 sn).
- DER ~%43.3 (auto sonucundan daha kötü).
- Sonuç: Sorun yalnızca konuşmacı sayısının tahmin edilmesi değil.
- Not: Konuşmacı sayısı verildiğinde pyannote, VBx yerine KMeans kullanıyor.

**2. Speaker embedding teşhisi** (referans turlardan Community-1 embedding'leri):
- A ve B belirgin biçimde ayrışıyor:
  - Aynı konuşmacı benzerliği (A-A / B-B): ~0.60–0.65.
  - Farklı konuşmacı benzerliği (A-B): ~0.16–0.19.
  - Aynı-konuşmacı çiftinin A-B çiftinden daha benzer olma olasılığı (AUC): ~0.999.
  - Her turun en benzer turu 13/13 kez aynı konuşmacı.
- Zaman kaynaklı kayma (drift) gözlenmedi.
- Ham embedding uzayında ve PLDA uzayında aynı sonuç.
- Bu bulgu 4. teşhisle doğrulandı: sorun embedding modelinde değil.

**3. Dışarıdan ayarlanabilen seçenekler** (henüz hiçbiri değiştirilmedi):
- Çağrı parametreleri: `num_speakers`, `min_speakers`, `max_speakers`.
- `pipeline.instantiate` ile: `clustering.threshold` (0.6), `clustering.Fa` (0.07), `clustering.Fb` (0.8), `segmentation.min_duration_off` (0.0).
- Ürün koduna taşımak `diarization/` değişikliği gerektirir.

**4. Gerçek pipeline embedding analizi** (public `hook` ile; hook'lu çalıştırmanın çıktısı ürünle birebir aynı):
- Community-1 akışı:
  - Segmentasyon 10 sn pencere, 1 sn adım, 3 yerel konuşmacı slotu (aynı anda en fazla 2).
  - Her (pencere, slot) için bir embedding üretiliyor: 10 sn'lik ses WeSpeaker ResNet34'ten geçiyor, slot maskesi yalnızca istatistik havuzlamada ağırlık olarak kullanılıyor. `embedding_exclude_overlap: true`.
  - Clustering'e yalnızca slotun pencerede ≥%20 tek başına konuştuğu embedding'ler gidiyor. AHC (0.6) → PLDA → VBx (Fa 0.07, Fb 0.8). Pencere içinde kısıtlı atama: iki slot aynı kümeye gidemiyor.
- three_speakers'ta 44 × 3 = 132 embedding var; 52'si clustering'e gidiyor.
- **44 pencerenin 33'ünde A ile B aynı yerel slotta.** Clustering'e giden 42 A/B embedding'inin 38'i iki konuşmacıyı içeren maskeden üretiliyor.
- Pipeline içinde A/B AUC ~0.62, A-B benzerliği ~0.557 (saf turlarda 0.999 / 0.19).
- Embedding, maskedeki A/B oranını izliyor (r = 0.964). Temiz maskeli az sayıdaki embedding saf turlar kadar iyi. Yani embedding çıkarıcı sağlam; girdi karışık.
- Slot permütasyonu (pencereler arası slot değişimi) neden değil.
- Clustering ikincil: AHC 7 küme buluyor, VBx 2'ye indiriyor. Aynı segmentasyonla kusursuz (oracle) clustering bile DER ~%34.7 / confusion ~%23.1 verirdi.
- `num_speakers=3` denemesindeki "zamana göre bölünme" de bu karışımdan kaynaklanıyor: pencere kaydıkça A:B oranı yavaşça değişiyor.
- **Sonuç: Ana problem segmentation / local speaker slot contamination.**

**5. Slot-free teşhis** (yalnızca teşhis; ürün koduna alınmadı):
- Yöntem:
  - Konuşma bölgeleri: pipeline'ın kendi `speaker_counting` çıktısı (count > 0).
  - Slot maskeleri ve slot ataması kullanılmıyor.
  - Bölgeler 1.5 sn pencere / 0.75 sn adımla bölünüyor. 1.5 sn'den kısa bölge tek pencere; bölge sonu artakalırsa sona hizalı bir pencere daha ekleniyor.
  - Her pencerede aynı WeSpeaker modeliyle maskesiz tek embedding çıkarılıyor.
  - Clustering: pipeline'ın kendi `pipeline.clustering` nesnesi (AHC 0.6 / PLDA / VBx Fa 0.07, Fb 0.8) değiştirilmeden kullanılıyor. Pencere başına tek embedding olduğu için kısıtlı atama etkisiz kalıyor.
  - Zaman çizgisi: 10 ms karelerde, kareyi kapsayan pencerelerin kümeleri arasında çoğunluk oyu; eşitlikte merkezi kareye en yakın pencere.
- three_speakers sonucu:

  | | Baseline | Slot-free |
  |---|---|---|
  | Konuşmacı (GT 3) | 2 | **3** |
  | DER | ~%41.06 | **~%11.43** |
  | Konuşmacı karışması | ~%29.5 | **%0** |
  | Kaçırılan konuşma | ~%11.45 | ~%11.31 |
  | Yanlış alarm | ~%0.11 | ~%0.13 |
  | A/B AUC | ~0.62 | **~0.971** (A-B benzerliği ~0.148) |

- Kısıt: Bu kayıtta her konuşmacı değişiminde sessizlik var; her konuşma bölgesi tek bir tura denk geliyor. Bu yüzden hızlı tur değişimi burada test edilmedi.
- Teşhis script'leri repo dışında, geçici scratch alanında kaldı. Yöntem yukarıda tarif edildi; gerektiğinde yeniden yazılır.

**6. 2 konuşmacılı regresyon** (`two_speakers_clean.wav`, slot-free; GT yok, baseline yalnızca karşılaştırma için kullanıldı):
- 2 konuşmacı bulundu; gereksiz 3. veya 4. konuşmacı oluşmadı. Kümeler dengeli (27 / 26 pencere).
- Baseline'ın tek konuşmacılı olduğu karelerin ~%97.3'ünde uyum var; ana konuşmacı değişimleri korunuyor.
- Dikkat edilecekler:
  - Sessizliksiz gelen kısa karşılıklar ana konuşmacıya yazılabiliyor (~0.3–0.5 sn'lik iki örnek).
  - Çakışma temsil edilemiyor (her kareye tek konuşmacı). Ürüne alınırsa **D-011 ile çelişir**; karar güncellemesi gerekir.
  - Sınır zamanları ±0.3 sn oynayabiliyor.

**7. Yeni bağımsız test kaydı:** `tests/data/two_speakers_v2.wav`
- ~32.0 sn, WAV PCM 16-bit, 48 kHz, stereo (pratikte ikili mono).
- Peak −3.1 dBFS, clipping yok, NaN/Inf yok.
- Salt-okunur dalga formu karşılaştırmasıyla `three_speakers.wav` ve `two_speakers_clean.wav`'dan bağımsız olduğu doğrulandı (en yüksek normalize korelasyon ~0.23).
- Henüz GT yok; baseline ve slot-free için sayısal benchmark yapılmadı.
- Not: Yereldeki `two_speakers_eskisininkopyasi.wav` bağımsız değil; `three_speakers.wav`'ın ilk ~41 sn'sinin (A/B bölümü) kopyası. Test kaydı olarak kullanılmaz.

## Test Sonuçları (2026-09-24)
- **Birim testleri: 56/56 geçti.**
  - Cihaz seçimi: 11
  - Normalizasyon: 8
  - Kelime eşleme: 11
  - API (sahte modellerle): 6
  - Kalite metrikleri: 20
- **Entegrasyon testleri: 6 geçti, 2 başarısız, 6 skip.**
  - Başarısız: `test_three_speakers[auto]` ve `test_three_speakers[cpu]`; 3 yerine 2 konuşmacı. Bilinen diarization sorunu.
  - Geçenler:
    - 2 konuşmacı testi (`auto` ve `cpu`)
    - GPU/CPU konuşmacı sayısı tutarlılığı (iki kayıt)
    - Transcriber
    - Gerçek modellerle API
  - Skip edilenler: `short_utterances.wav` ve `overlap.wav` yok (3'er test).
- **Frontend:** `npm run build` başarılı. Manuel test (dosya seçme, yükleme durumu, sonuç, boş metin, 400 hatası, backend kapalı) geçti.

## Bilinen Sınırlamalar
Konuşmacı sınırı ve boş segmentlerle ilgili maddeler D-020 kapsamında hâlâ kabul edilmiş durumda. V1.1 kalite çalışması bu sınırlamaları ölçüyor.
- **Konuşmacı birleşmesi:** Diarization bazı kayıtlarda farklı konuşmacıları tek konuşmacıda birleştiriyor (three_speakers: A + B). Neden: segmentasyon A ile B'yi aynı yerel slota koyuyor (bkz. teşhis 4).
- **Konuşmacı sınırında kelime kayması:** Whisper'ın kelime zamanları sapabildiği için sınırdaki kelimeler komşu konuşmacıya atanabilir.
- **Boş kısa segmentler:** Kısa diarization segmentleri (ör. 0.07 sn'lik parçalar) ve çakışma bölgeleri `text: ""` ile kalabilir.
- **Tolerans dışı kelimeler:** Hiçbir segmente 0.5 sn'den yakın olmayan kelimeler çıktıya girmez. Şimdiye kadarki kayıtlarda böyle bir kelime olmadı.
- **Overlap:** Aynı anda konuşmada Whisper çoğunlukla baskın sesi yazar.
- **Süre ve bellek:**
  - İstekler senkron ve sırayla işleniyor. CPU'da uzun kayıtlar çok yavaş olabilir.
  - GPU'da ayrılmış bellek 8 GB'ın ~7 GB'ına ulaşıyor; çok uzun kayıtlarda bellek sınırı zorlanabilir.
  - Tüm ses belleğe okunuyor.
- **Güvenlik:** API'de kimlik doğrulama yok; yalnızca yerelde (`127.0.0.1`) çalıştırılmalı.

## Kapsam Dışı / Henüz Yok
- SQLite / veritabanı, analiz geçmişi, JSON İndir (V1.1'de planlandı, henüz yok)
- Minimal yerel `GET /health` ve `POST /diarize` dışındaki API özellikleri (kimlik doğrulama, ağa açma, kuyruk vb.)
- Frontend V0 dışındaki arayüz özellikleri: login, audio player, waveform, transkript editörü
- Ağ (networking)
- Fiziksel cihaz entegrasyonu
- Konuşmacı kimliği tanıma
- LLM özellikleri
- Canlı mikrofon / gerçek zamanlı streaming implementasyonu

## Git Çalışma Akışı
- Geliştirme doğrudan `main` dalında yapılır; ayrı feature branch açılmaz (D-023).
- `milestone-1-diarization` dalı 2026-09-24'te `main`'e fast-forward ile alındı.
- Commit ve push yalnızca kullanıcı onayıyla yapılır. Öncesinde test, `git diff`, `git status`, token/secret ve ignore kontrolleri yapılır.

## Sonraki Adım
1. `tests/data/two_speakers_v2.reference.json` dosyasını insan eliyle, sesi dinleyerek bağımsız hazırlamak (hiçbir sistem çıktısından türetmeden).
2. Community-1 baseline benchmark (`quality.benchmark`).
3. Slot-free benchmark (teşhis script'i, yukarıdaki 5. maddedeki yöntemle).
4. DER / confusion / missed / FA karşılaştırması.
5. Sonuç iyiyse slot-free yaklaşımın ürün pipeline'ına alınmasını planlamak. D-005, D-011 ve ilgili kararlarla çelişkiler açıkça ele alınacak.
