# Toplantı Asistanı

Zamanla fiziksel bir ses yakalama cihazını bilgisayar tarafındaki AI işlemeyle birleştirecek bir toplantı sesi projesi.

## Mevcut Durum

Proje ilk geliştirme milestone'unda.

Şu anki hedef yalnızca şu:

> Kayıtlı sesten speaker diarization.

Bir toplantı kaydı verildiğinde modül, her zaman aralığında hangi anonim konuşmacının konuştuğunu belirlemeli.

Örnek:

```text
00:00 - 00:04 → SPEAKER_00
00:04 - 00:09 → SPEAKER_01
00:09 - 00:13 → SPEAKER_00
```

## Mevcut Kapsam

İlk modül:

- Kayıtlı sesi girdi olarak alacak.
- Speaker diarization çalıştıracak.
- Anonim konuşmacı etiketleri döndürecek.
- Başlangıç/bitiş zaman damgalarını döndürecek.
- Sonuçları JSON uyumlu veriye normalize edecek.
- CUDA mevcutsa otomatik olarak kullanacak.
- Aksi halde CPU'ya geri dönecek.

## İlk Teknoloji

- Python
- PyTorch
- pyannote.audio
- `speaker-diarization-community-1`

## Henüz Implemente Edilmeyenler

- Speech-to-text
- Gerçek zamanlı streaming
- UI
- API
- Veritabanı
- Cihaz iletişimi
- Konuşmacı kimliği tanıma
- Toplantı özetleri
- LLM özellikleri

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
