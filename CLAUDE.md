# CLAUDE.md

## Rol
Bu projenin implementasyon asistanısın.
Açık onay olmadan kapsamı genişletme.

## Çalışma Yöntemi
Her anlamlı değişiklikte şu sırayı izle:

1. Mevcut kapsamı anla.
2. `PROJECT_BRAIN.md`, `CURRENT_STATE.md` ve `DECISIONS.md` dosyalarını oku.
3. İstendiğinde implementasyondan önce Plan Mode kullan.
4. Gereken en küçük değişikliği yap.
5. Değişikliği test et.
6. Sonucu doğrula.
7. İlgili proje MD dosyalarını güncelle.
8. Yalnızca doğrulamadan sonra commit et.

## Temel Kurallar
- Implementasyonları minimal ve odaklı tut.
- İlgisiz özellikler ekleme.
- Gereksiz refactor yapma.
- Gerekmedikçe çalışan kodu yeniden tasarlama.
- Erken abstraction yerine açık ve modüler kodu tercih et.
- Açıkça istenmedikçe UI, API, veritabanı, STT, LLM, ağ (networking) veya cihaz entegrasyonu ekleme.
- İleride canlı ses desteğiyle uyumluluğu koru, ancak henüz gerçek zamanlı streaming implementasyonu yapma.
- Bir görev test edilip doğrulanmadan tamamlandığını asla varsayma.
- Proje MD dosyalarını Türkçe tut; teknik terimler gerektiğinde İngilizce kalabilir.
- Hugging Face token'ını asla kaynak koda, MD dosyalarına, repoya veya commit geçmişine yazma. Erişim için `uv run hf auth login` veya güvenli bir ortam değişkeni kullanılır.

## Mevcut Teknik Yön
Projenin şu anki hedefi bağımsız (standalone) bir speaker diarization modülüdür.

Modül:
- Bir ses dosyasını girdi olarak almalı.
- Farklı konuşmacıları tespit etmeli.
- Konuşmacıları `SPEAKER_00`, `SPEAKER_01` vb. olarak etiketlemeli.
- Her konuşmacı segmenti için başlangıç ve bitiş zaman damgalarını döndürmeli.
- Normalize edilmiş, JSON uyumlu bir çıktı üretmeli.
- CUDA mevcut olduğunda GPU kullanmalı.
- CUDA mevcut olmadığında CPU'ya geri dönmeli (fallback).
- `auto`, `cpu` veya `cuda` ile açık cihaz seçimini desteklemeli.
- İlk diarization yaklaşımı olarak `pyannote.audio` ile `speaker-diarization-community-1` kullanmalı.

Kullanıcı onayıyla, diarization modülü değiştirilmeden üzerine şunlar eklendi:
- `openai-whisper` (`turbo` modeli, sabit Türkçe) ile kelime zaman damgalı speech-to-text.
- Whisper kelimelerinin diarization segmentlerine zaman örtüşmesiyle eşlenmesi (örtüşmeyen kelimeler için en fazla 0.5 sn tolerans).
- Yalnızca yerel (127.0.0.1) çalışan minimal FastAPI backend: `POST /diarize` konuşmacılı transkripti döndürür ve `outputs/` altına JSON olarak kaydeder.

## Şimdilik Kapsam Dışı
- Ahmet/Mehmet gibi konuşmacı kimliği tanıma
- UI
- Minimal yerel `POST /diarize` endpoint'i dışındaki API özellikleri (kimlik doğrulama, ağa açma, kuyruk vb.)
- Veritabanı
- Wi-Fi
- Bluetooth
- Cihaz firmware'i
- Toplantı özetleme
- LLM özellikleri
- Gerçek zamanlı streaming implementasyonu

## Test Felsefesi
İlk faydalı testler şunları kapsamalı:
- Temiz 2 konuşmacılı ses
- 3 konuşmacılı ses
- Kısa konuşmalar
- Üst üste binen konuşmalar (overlapping speech)

Varsayılan akışta konuşmacı sayısını sabit kodlama.
İsteğe bağlı konuşmacı sayısı kısıtları ileride desteklenebilir.
