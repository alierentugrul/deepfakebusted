# Rapor İskeleti — DeepFakeBusted

## 1. Giriş
- Deepfake teknolojisinin yaygınlaşması ve güvenlik riski
- Çalışmanın amacı: farklı derin öğrenme modellerini karşılaştırmak ve canlı tahmin sistemi geliştirmek
- Nihai katkı: yalnızca kapalı test başarısını değil, dağılım dışı genellemeyi de incelemek

## 2. Veri Setleri
### 2.1 Ana veri seti
- 140k Real and Fake Faces
- Train / valid / test yapısı
- Görüntü tabanlı ikili sınıflandırma

### 2.2 Dış veri seti
- DF40 tabanlı dış veri alt kümesi
- 16.060 real + 16.060 fake
- Amaç: görülmemiş deepfake türlerine karşı genelleme ölçümü

## 3. Yöntem
- Ön işleme: görüntü yeniden boyutlandırma, normalization, canlı tahminde yüz kırpma
- Modeller: MesoNet, ResNet-50, EfficientNet-B4, Xception, ViT-B/16
- Eğitim stratejisi: transfer learning, AdamW, cosine scheduler, mixed precision, early stopping
- Değerlendirme metrikleri: Accuracy, AUC-ROC, F1, Precision, Recall, inference time

## 4. İlk Deney Sonuçları
- Kapalı test setinde model karşılaştırması
- Xception'ın en iyi modellerden biri olarak öne çıkması
- Ancak profesyonel / dış örneklerde zayıflık gözlenmesi

## 5. Genelleme Problemi ve İkinci Aşama
- Eski Xception:
  - Orijinal test accuracy: %99.73
  - Dış test accuracy: %52.74
  - Dış test fake recall: %6.04
- Yeni Xception + DF40 dış veri:
  - Orijinal test accuracy: %99.10
  - Dış test accuracy: %92.15
  - Dış test fake recall: %84.50
- Yorum: az miktarda in-domain kayıp karşılığında çok büyük out-of-distribution kazanım

## 6. Web Uygulaması
- Flask API + React/Vite arayüzü
- Canlı analiz
- Tüm modellerle karşılaştırma
- Eğitim/değerlendirme grafikleri
- Yüz kırpma ön izlemesi

## 7. Sınırlılıklar
- Görüntü tabanlı çalışma; video-zamansal ipuçları kullanılmıyor
- Tüm deepfake üretim teknikleri kapsanmıyor
- Dış veri seti hâlâ sınırlı bir alt küme
- Yüz kırpma bazen bağlamsal ipuçlarını azaltabilir

## 8. Gelecek Çalışmalar
- AI-Face, DFFD, Celeb-DF v2 ve DF40 ile daha geniş eğitim
- Multi-crop inference ve ensemble
- SBI / CLIP tabanlı generalization odaklı detector'lar
- Video tabanlı tespit
- Hard-set ve gerçek dünya benchmark'larının genişletilmesi

## 9. Sonuç
- Kapalı test başarısının tek başına yeterli olmadığı gösterildi
- Dış veri eklenerek nihai modelin gerçek dünyaya genellemesi belirgin biçimde iyileştirildi
- DeepFakeBusted, hem araştırma hem demo açısından olgunlaştırılmış bir bitirme projesine dönüştü
