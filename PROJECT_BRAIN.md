# PROJECT_BRAIN.md

## Proje Özeti
Bu proje, fiziksel bir ses yakalama cihazı etrafında kurulan bir toplantı asistanı sistemine dönüşmeyi hedefliyor.

Fiziksel cihaz öncelikle toplantı sesini toplayacak ve bir bilgisayara gönderecek.
AI işlemlerini bilgisayar yapacak.

Uzun vadede sistem şunları destekleyebilir:
- Kayıtlı toplantılar
- Canlı toplantılar
- Speaker diarization
- Speech-to-text
- Toplantı özetleri
- Kararlar ve aksiyon maddeleri
- Cihazdan PC'ye ses aktarımı

Ancak geliştirme aşamalı olarak ilerleyecek.

---

## Mevcut Ürün Mimarisi

```text
Toplantı Odası
    ↓
Mikrofon / Mikrofon Dizisi
    ↓
Fiziksel Cihaz
    ↓
Ses Aktarımı
    ↓
Bilgisayar
    ↓
AI İşleme
```

İlk mimaride cihazın ağır AI inference yapması beklenmiyor.

---

## Mevcut Geliştirme Hedefi

İlk milestone, bağımsız (standalone) bir speaker diarization modülüdür.

Girdi:

```text
audio.wav
```

Çıktı örneği:

```json
[
  {
    "speaker": "SPEAKER_00",
    "start": 0.52,
    "end": 4.81
  },
  {
    "speaker": "SPEAKER_01",
    "start": 4.94,
    "end": 9.27
  }
]
```

İlk sürümün Ahmet, Mehmet veya Ayşe gibi gerçek kimlikleri bilmesi gerekmiyor.

---

## Terminoloji

### Speaker Diarization
Şu soruyu yanıtlar:

> Kim, ne zaman konuştu?

Örnek:

```text
00:00 - 00:04 → SPEAKER_00
00:04 - 00:09 → SPEAKER_01
```

### Speaker Identification
Şu soruyu yanıtlar:

> Bu kişi kim?

Örnek:

```text
SPEAKER_00 → Kerem
```

Speaker identification şu anda kapsam dışıdır.

### Speaker Separation
Üst üste binen konuşmacıları ayrı ses sinyallerine ayırır.

Bu, şu anki birincil hedef değildir.

---

## İlk Teknoloji Yönü

### Dil
Python

### Diarization
`pyannote.audio`

İlk model:

`pyannote/speaker-diarization-community-1`

### Hesaplama Stratejisi

Varsayılan:

```text
device = auto
```

Davranış:

```text
CUDA mevcut → GPU
CUDA mevcut değil → CPU
```

Implementasyon yalnızca CPU bulunan sistemlerde de kullanılabilir kalmalı.

---

## Tasarım İlkesi

İlk implementasyon kayıtlı ses dosyalarını işleyecek.

Ancak dahili modül, ileride canlı ses desteği eklemeyi gereksiz yere zorlaştıracak varsayımlardan kaçınmalı.

Henüz streaming implementasyonu yapma.

İleride mimari şu gibi ayrı metotlar sunabilir:

```text
diarize_file(...)
diarize_stream(...)
```

Mevcut milestone'a yalnızca dosya tabanlı akış dahildir.

---

## İlk Milestone Başarı Kriterleri

Milestone şu koşullar sağlandığında başarılı sayılır:

- Bir ses dosyası verilebiliyor.
- Diarization modeli başarıyla çalışıyor.
- Birden fazla konuşmacı tespit ediliyor.
- Konuşmacı ID'leri döndürülüyor.
- Başlangıç zaman damgaları döndürülüyor.
- Bitiş zaman damgaları döndürülüyor.
- Sonuçlar JSON uyumlu yapılara normalize ediliyor.
- CUDA mevcutsa otomatik olarak kullanılıyor.
- CPU fallback çalışıyor.
- En az 2 konuşmacılı ve 3 konuşmacılı örnekler test edilmiş.

---

## Şu Anki Hedef Dışı Konular

Henüz implemente etme:

- Speech-to-text
- Whisper
- Gerçek zamanlı streaming
- UI
- REST API
- Veritabanı
- Kullanıcı hesapları
- Wi-Fi iletişimi
- Bluetooth iletişimi
- Firmware
- Konuşmacı ismi tanıma
- Toplantı özetleri
- Aksiyon maddesi çıkarımı
- LLM entegrasyonu
