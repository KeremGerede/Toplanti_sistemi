# DECISIONS.md

## D-001 — Cihazın Rolü
**Karar:** Fiziksel cihaz öncelikle ses toplayacak. Ağır AI işlemleri bilgisayarda çalışacak.

**Gerekçe:** Donanımı daha basit tutar ve ses yakalama problemlerini AI inference problemlerinden ayırır.

---

## D-002 — Konuşmacı Etiketleri
**Karar:** İlk sürüm `SPEAKER_00` ve `SPEAKER_01` gibi anonim konuşmacı etiketleri kullanacak.

**Gerekçe:** Gerçek kişilerin sesinden tanınması ilk milestone için gereksizdir ve ek karmaşıklık getirir.

---

## D-003 — İlk Diarization Modu
**Karar:** Kayıtlı ses dosyalarıyla başla.

**Gerekçe:** Çevrimdışı ses, işin içine streaming, ağ veya donanım problemlerini katmadan diarization kalitesini doğrulamanın en hızlı yoludur.

---

## D-004 — İleride Canlı Destek
**Karar:** Gerçek zamanlı diarization'ı henüz implemente etme, ancak ileride eklenmesini gereksiz yere engelleyecek mimari tercihlerden kaçın.

**Gerekçe:** Canlı diarization ayrı bir teknik problemdir ve ilk milestone'un kapsamını büyütmemelidir.

---

## D-005 — İlk Diarization Yığını
**Karar:** `pyannote.audio` ve `speaker-diarization-community-1` ile başla.

**Gerekçe:** Yerel speaker diarization için pratik bir başlangıç noktası sağlar ve ekibin ürün konseptini hızlıca doğrulamasına olanak tanır.

---

## D-006 — Hesaplama Cihazı Stratejisi
**Karar:** Otomatik cihaz seçimi kullan.

Beklenen davranış:

```text
CUDA mevcut → cuda
CUDA mevcut değil → cpu
```

İleride desteklenecek konfigürasyon:

```text
auto
cpu
cuda
```

**Gerekçe:** NVIDIA GPU'lu geliştirme makineleri hızlandırmadan faydalanmalı, yalnızca CPU bulunan ortamlar da desteklenmeye devam etmeli.

---

## D-007 — Varsayılan Konuşmacı Sayısı
**Karar:** Varsayılan iş akışında konuşmacı sayısını zorunlu tutma veya sabit kodlama.

**Gerekçe:** Gerçek toplantılarda konuşmacı sayısı bilinmeyebilir.

`num_speakers`, `min_speakers` veya `max_speakers` gibi isteğe bağlı kısıtlar ileride değerlendirilebilir.

---

## D-008 — Çıktı Sözleşmesi
**Karar:** Diarization sonuçlarını, modele özgü nesneleri doğrudan dışarı açmak yerine projeye ait JSON uyumlu yapılara normalize et.

Örnek:

```json
[
  {
    "speaker": "SPEAKER_00",
    "start": 0.52,
    "end": 4.81
  }
]
```

**Gerekçe:** Bu, ileride uygulamanın geri kalanını diarization sağlayıcısından yalıtır ve sonraki STT entegrasyonunu kolaylaştırır.

---

## D-009 — Geliştirme Yöntemi
**Karar:** Proje MD iş akışını kullan:
- `CLAUDE.md`
- `PROJECT_BRAIN.md`
- `CURRENT_STATE.md`
- `DECISIONS.md`
- `README.md`

Geliştirme sırası:

```text
plan → uygula → test et → doğrula → dokümanları güncelle → commit
```

**Gerekçe:** Claude oturumlarını tutarlı tutar ve proje bağlamını geliştirme oturumları arasında korur.

---

## D-010 — Ses Okuma
**Karar:** Ses dosyası `soundfile` ile belleğe okunur ve modele `{"waveform", "sample_rate"}` olarak verilir. FFmpeg kullanılmaz.

**Gerekçe:** pyannote.audio 4'ün kendi dosya okuma yolu (`torchcodec`), Windows'ta FFmpeg'in "shared" sürümünü gerektiriyor. Bellekten ses verme bu bağımlılığı kaldırır ve ileride canlı ses parçalarının da aynı çekirdeğe verilebilmesine uygundur.

---

## D-011 — Diarization Çıktı Kaynağı
**Karar:** pyannote'un `speaker_diarization` çıktısı kullanılır; `exclusive_speaker_diarization` kullanılmaz. Farklı konuşmacılara ait çakışan segmentler korunur.

**Gerekçe:** Aynı anda konuşma (overlap) bilgisi kaybolmaz ve overlap senaryosu gözlemlenebilir.

---

## D-012 — Konuşmacı Etiketlerinin Sırası
**Karar:** Etiketler, konuşmacıların ilk konuşma sırasına göre `SPEAKER_00`, `SPEAKER_01` … olarak yeniden atanır.

**Gerekçe:** Çıktı deterministik olur ve modelin kendi etiketleme düzeninden bağımsız kalır (D-008).

---

## D-013 — Açık `cuda` İsteği
**Karar:** `auto`, CUDA varsa `cuda`, yoksa `cpu` seçer. `cuda` açıkça istenip CUDA yoksa `RuntimeError` verilir; sessizce CPU'ya düşülmez.

**Gerekçe:** Açık bir cihaz isteği karşılanamadığında kullanıcı bunu fark etmeli.

---

## D-014 — Telemetri
**Karar:** pyannote.audio telemetrisi kod içinde kapatılır (`set_telemetry_metrics(False)`).

**Gerekçe:** Proje toplantı kayıtlarıyla çalışıyor; gizlilik varsayılan olmalı.

---

## D-015 — Dokümantasyon Dili
**Karar:** Proje MD dosyaları Türkçe tutulur. Teknik terimler gerektiğinde İngilizce kalabilir.

**Gerekçe:** Ekibin çalışma dili Türkçe.

---

## D-016 — Hugging Face Token Güvenliği
**Karar:** HF token hiçbir zaman kaynak koda, MD dosyalarına, repoya veya commit geçmişine yazılmaz. Token `uv run hf auth login` önbelleğinden ya da güvenli bir ortam değişkeninden (`HF_TOKEN`) okunur. CLI'da `--token` argümanı yoktur. Her commit'ten önce token taraması yapılır.

**Gerekçe:** Token sızıntısını ve shell geçmişine düşmesini önlemek.

---

## D-017 — Test Kayıtları
**Karar:** Test ses kayıtları `tests/data/` altında tutulur ama commit edilmez (`.gitignore`). Beklenen dosyalar `tests/data/README.md` içinde açıklanır. Kayıt yoksa entegrasyon testleri skip edilir.

**Gerekçe:** Gizlilik ve repo boyutu.

---

## D-018 — Kısa Konuşma ve Overlap Testleri
**Karar:** Temiz 2 konuşmacılı ve 3 konuşmacılı kayıtlarda konuşmacı sayısı zorunlu başarı kriteridir. Kısa konuşma ve overlap senaryoları bu aşamada eşik değil, gözlem/baseline olarak değerlendirilir.

**Gerekçe:** Bu aşamanın amacı çalışan bir modül kurmak; zor senaryolardaki kalite önce ölçülmeli.

---

## D-019 — Speech-to-text
**Karar:** Kullanıcı onayıyla kapsam genişletildi ve speech-to-text eklendi. `openai-whisper`, `turbo` (large-v3-turbo) modeli ve sabit Türkçe (`language="tr"`) kullanılır. Transkripsiyon tüm ses için bir kez, kelime zaman damgalarıyla yapılır.

**Gerekçe:** Kurulu CUDA torch'u kullanıyor; Windows'ta ek DLL veya FFmpeg gerektirmiyor. `faster-whisper` Windows GPU kurulumu için riskli bulundu. `turbo`, 8 GB GPU'da diarization modeliyle birlikte sığıyor ve kalitesi bu aşama için yeterli bulundu.

---

## D-020 — Kelimelerin Konuşmacı Segmentleriyle Eşlenmesi
**Karar:**
- Her Whisper kelimesi, zaman olarak en çok örtüştüğü diarization segmentine atanır.
- Örtüşme eşitse listede önce gelen segment seçilir.
- Hiçbir segmentle örtüşmeyen kelime, en yakın segmente en fazla 0.5 sn (`MAX_GAP_SECONDS`) uzaktaysa ona atanır; daha uzaktaysa hiçbir konuşmacıya atanmaz.
- Kelime almayan segmentler `text: ""` ile korunur.
- Konuşmacı sınırlarındaki kelime kaymaları ve boş kısa segmentler şimdilik bilinen sınırlamadır; bunları düzeltmek için ek mantık eklenmez.

**Gerekçe:** Basit ve açıklanabilir bir kural. Kelimeyi yanlış konuşmacıya atamak yerine, emin olunamayan kelimenin kaybedilmesi tercih edildi.

---

## D-021 — Konuşmacılı Transkript Çıktı Sözleşmesi
**Karar:** Yerel API ve `outputs/` dosyaları şu formatı kullanır:

```json
{
  "source_file": "meeting.wav",
  "speaker_count": 2,
  "segments": [
    {"speaker": "SPEAKER_00", "start": 0.82, "end": 5.41, "text": "..."}
  ]
}
```

`speaker_count`, segmentlerdeki farklı konuşmacı sayısıdır. Diarization modülünün kendi çıktısı için D-008 (bare list) aynen geçerlidir.

**Gerekçe:** Transkript kendi kaynağını ve konuşmacı sayısını taşır. Diarization modülü değiştirilmeden kalır.

---

## D-022 — Yerel API ve `outputs/`
**Karar:**
- FastAPI ile minimal bir backend kurulur. Uç noktalar: `GET /health` ve `POST /diarize`.
- `POST /diarize` multipart dosya alır ve diarization, transcription ve alignment adımlarının hepsini yapar. Endpoint adı şimdilik korunuyor; isim değişikliği daha sonra değerlendirilecek.
- Sunucu yalnızca `127.0.0.1` üzerinde çalışır. Kimlik doğrulama yoktur.
- İki model de başlangıçta bir kez, `APP_DEVICE` (`auto`/`cpu`/`cuda`) ile seçilen cihaza yüklenir. İstekler bir kilit ile sırayla işlenir.
- Yüklenen ses yalnızca işlem süresince geçici dosyada tutulur, sonra silinir.
- Sonuç `outputs/<zaman>_<dosya_adı>.json` olarak kaydedilir. `outputs/` içeriği commit edilmez.

**Gerekçe:** Diarization ve transkripti tek bir çağrıyla kullanmak için en küçük arayüz. Gizlilik nedeniyle ses saklanmaz ve sunucu ağa açılmaz.
