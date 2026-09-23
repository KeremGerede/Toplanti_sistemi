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
