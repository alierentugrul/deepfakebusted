# Sunum Akışı — 8 Slayt

## 1. Problem
**Başlık:** Deepfake neden zor bir problem?
- Gerçekçi üretimler artıyor
- Güvenlik ve doğrulama ihtiyacı büyüyor

## 2. Proje hedefi
**Başlık:** Ne inşa ettim?
- Birden fazla modeli karşılaştıran sistem
- Canlı görüntü analizi yapan web demo

## 3. Veri ve mimari
**Başlık:** Sistem nasıl çalışıyor?
- Ana veri seti
- Yüz kırpma
- Eğitim ve değerlendirme pipeline'ı

## 4. İlk model karşılaştırması
**Başlık:** Kapalı test setinde kim kazandı?
- MesoNet / ResNet / EfficientNet / Xception tablosu
- Xception'ın güçlü performansı

## 5. Kritik kırılma
**Başlık:** Yüksek doğruluk neden yetmedi?
- Eski Xception dış testte %52.74
- Fake recall yalnızca %6.04

## 6. İyileştirme
**Başlık:** Dış veri ile yeniden eğitim
- DF40 tabanlı dış veri ekleme
- Yeni modelin sonuçları

## 7. Demo
**Başlık:** Canlı sistem
- Görsel yükleme
- Model seçimi
- Tüm modellerle karşılaştırma

## 8. Sonuç
**Başlık:** Asıl kazanım neydi?
- Orijinal testte %99.10
- Dış testte %92.15
- Genelleme, ham doğruluktan daha kıymetli
