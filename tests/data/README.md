# Test Ses Kayıtları

Bu klasör entegrasyon testlerinde kullanılan ses kayıtları içindir.

**Gerçek ses dosyaları GitHub'a commit edilmez.** Gizlilik ve repo boyutu nedeniyle `.gitignore` ile dışarıda bırakılır; bu klasörde yalnızca bu README takip edilir. Her geliştirici kayıtları kendi makinesinde bu klasöre koyar. Dosyalar yoksa entegrasyon testleri otomatik olarak atlanır (skip).

## Önerilen format

- WAV, 16 kHz veya üzeri
- Mono veya stereo olabilir

## Beklenen dosyalar

### `two_speakers_clean.wav`
- **Amaç:** Temel doğruluk kontrolü.
- **Süre:** ~30–60 sn
- **Konuşmacı sayısı:** 2
- **Senaryo:** Sessiz bir ortamda iki kişi sırayla 3–10 sn'lik turlarla konuşur. Üst üste konuşma yoktur.

### `three_speakers.wav`
- **Amaç:** İkiden fazla konuşmacının ayrıştırılması.
- **Süre:** ~45–90 sn
- **Konuşmacı sayısı:** 3
- **Senaryo:** Üç kişi sırayla konuşur. Üst üste konuşma yoktur ya da çok azdır.

### `two_speakers_v2.wav`
- **Amaç:** Bağımsız ikinci bir 2 konuşmacılı kontrol (baseline ile slot-free teşhisinin karşılaştırılması).
- **Süre:** ~32 sn
- **Konuşmacı sayısı:** 2
- **Durum:** Yerelde mevcut. `three_speakers.wav` ve `two_speakers_clean.wav`'dan bağımsız olduğu doğrulandı. Referansı henüz hazırlanmadı.

### `short_utterances.wav`
- **Amaç:** Kısa araya girmelerin yakalanıp yakalanmadığını gözlemlemek.
- **Süre:** ~30–60 sn
- **Konuşmacı sayısı:** 2
- **Senaryo:** Bir kişi uzun konuşur. Diğer kişi en az 3 kez 0.5–1.5 sn'lik kısa ifadelerle ("evet", "tamam", "hı hı") araya girer.

### `overlap.wav`
- **Amaç:** Aynı anda konuşmanın (overlapping speech) çıktıda nasıl göründüğünü gözlemlemek.
- **Süre:** ~30–60 sn
- **Konuşmacı sayısı:** 2
- **Senaryo:** İki kişi konuşur. En az bir yerde 2–5 sn boyunca ikisi aynı anda konuşur.

## Referans (ground truth) dosyaları

Kalite ölçümü için her kayda, gerçekte kimin ne zaman ne söylediğini anlatan bir referans dosyası hazırlanır:

```text
tests/data/<kayıt_adı>.reference.json
```

Hazır referans: `three_speakers.reference.json`. Sıradaki referans: `two_speakers_v2.reference.json`.

**Referans dosyaları commit edilmez.** Gerçek konuşma içeriği barındırdıkları için `.gitignore` ile dışarıda bırakılır ve yerelde kalır.

### Format

Transkript çıktısıyla aynı yapıdadır:

```json
{
  "source_file": "two_speakers_clean.wav",
  "speaker_count": 2,
  "segments": [
    {
      "speaker": "A",
      "start": 0.8,
      "end": 7.3,
      "text": "..."
    }
  ]
}
```

- `source_file`: ses dosyasının adı.
- `speaker_count`: kayıttaki gerçek konuşmacı sayısı.
- `segments`: konuşma turları.
  - `speaker`: konuşmacı etiketi.
  - `start`, `end`: saniye cinsinden başlangıç ve bitiş zamanı.
  - `text`: turda söylenen metin.

### Yazım kuralları

- Konuşmacı değiştiğinde yeni bir tur başlar.
- "evet", "tamam", "hı hı" gibi kısa tepkiler kendi başlangıç ve bitiş zamanlarıyla ayrı bir tur olarak yazılır.
- Konuşmacı etiketleri serbesttir; `A`, `B`, `C` gibi etiketler kullanılabilir. Pipeline'ın `SPEAKER_xx` etiketleriyle eşleştirme ölçüm sırasında otomatik yapılır.
- Zamanlar sesi dinleyerek yaklaşık ±0.3 sn doğrulukla yazılabilir.
- Metin söylendiği şekilde yazılır. Sayılar rakamla yazılır (ör. `30`). Noktalama ve büyük/küçük harf serbesttir; ölçümde normalize edilir.
- Aynı anda konuşma (overlap) varsa iki konuşmacının turları zaman olarak çakışabilir.

**Referanslar sıfırdan hazırlanır.** Pipeline çıktısı taslak olarak kullanılmaz; mevcut hatalı çıktının yönlendirmemesi için önceki sonuçlara bakmadan, yalnızca sesi dinleyerek yazılır.

### Ölçüm

```powershell
uv run python -m quality.benchmark tests/data/two_speakers_clean.wav --reference tests/data/two_speakers_clean.reference.json
```

- Özet konsola yazılır. Raporlar `tests/data/results/` altına kaydedilir; bu klasör de commit edilmez.
- Modeller tekrar çalıştırılmadan yeniden puanlama için, kayıtlı hipotez dosyası `--hypothesis tests/data/results/<kayıt_adı>__baseline.hypothesis.json` ile verilir.
