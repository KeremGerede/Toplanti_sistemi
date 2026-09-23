# CURRENT_STATE.md

## Mevcut Aşama
Proje başlatma.

## Mevcut Milestone
İlk bağımsız speaker diarization modülünü geliştirmek.

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

## Başlanmamış
- Repository implementasyonu
- Python ortamı kurulumu
- Bağımlılık kurulumu
- Diarization servisi
- Cihaz seçim mantığı
- Sonuç normalizasyonu
- Test sesi hazırlığı
- Otomatik testler
- Benchmark'lar

## Kapsam Dışı
- STT
- UI
- API
- Veritabanı
- Ağ (networking)
- Fiziksel cihaz entegrasyonu
- Konuşmacı kimliği tanıma
- LLM özellikleri
- Canlı streaming implementasyonu

## Sonraki Adım
Proje bağlamını incelemek ve ilk diarization milestone'u için en küçük implementasyon planını önermek üzere Claude Plan Mode kullan.

Plan gözden geçirilmeden kod yazma.
