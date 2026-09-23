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
