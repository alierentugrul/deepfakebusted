# DeepFakeBusted Teknik Detay Notları

Bu dosya, akademik rapor ve savunma hazırlığı için projenin teknik ayrıntılarını özetler.

**DeepFakeBusted**, yüz görüntülerinin gerçek mi deepfake mi olduğunu sınıflandıran, birden fazla derin öğrenme modelini karşılaştıran ve özellikle **farklı veri setlerinde genelleme** problemini çözmeye çalışan bir sistemdir.

---

## 1. Projenin Temel Problemi

İlk hedef sadece “bir görüntü gerçek mi fake mi?” sorusunu yanıtlamaktı. Bunun için **140k Real and Fake Faces** veri seti üzerinde modeller eğitildi.

Fakat önemli bulgu şu oldu:

Ana test setinde Xception modeli **%99.73 doğruluk** verdi. Buna rağmen daha profesyonel, dış kaynaklı deepfake fotoğraflarda performans ciddi şekilde düştü. Bu durum şunu gösterdi:

> Model, aynı veri dağılımında çok başarılı olsa bile gerçek dünyadan gelen farklı deepfake örneklerine karşı zayıf kalabilir.

Bu nedenle proje sadece bir sınıflandırma projesi olmaktan çıkıp **genelleme başarımını artırma** projesine dönüştü.

---

## 2. Kullanılan Veri Setleri

### 2.1. Ana Veri Seti

Kullanılan ana veri seti:

**140k Real and Fake Faces**

Veri seti yapısı:

```text
train/
  real/
  fake/

valid/
  real/
  fake/

test/
  real/
  fake/
```

Sayılar:

| Bölüm | Real | Fake | Toplam |
|---|---:|---:|---:|
| Train | 50.000 | 50.000 | 100.000 |
| Validation | 10.000 | 10.000 | 20.000 |
| Test | 10.000 | 10.000 | 20.000 |

Etiketleme:

```text
real = 0
fake = 1
```

Model çıktısında özellikle `fake_probability`, yani sınıf 1’in softmax olasılığı kullanılmıştır.

---

### 2.2. Dış Veri Seti

Ana veri setindeki yüksek başarıya rağmen dış örneklerde zayıflama görüldüğü için DF40 tabanlı ek dış veri kullanılmıştır.

Dış veri yapısı:

| Bölüm | Real | Fake | Toplam |
|---|---:|---:|---:|
| Train | 12.848 | 12.848 | 25.696 |
| Validation | 1.606 | 1.606 | 3.212 |
| Test | 1.606 | 1.606 | 3.212 |

Bu veri ikinci veri kökü olarak eğitime eklenmiştir. Final eğitimde ana veri ve dış veri birlikte kullanılmıştır.

---

## 3. Ön İşleme Pipeline’ı

Görüntüler modelden önce standartlaştırılmıştır.

Eğitim aşamasında:

```text
Resize 256x256 civarı
RandomCrop 224x224
RandomHorizontalFlip
ColorJitter
RandomGrayscale
ToTensor
ImageNet normalization
```

Validation ve test aşamasında:

```text
Resize 224x224
ToTensor
ImageNet normalization
```

ImageNet normalizasyon değerleri:

```text
mean = [0.485, 0.456, 0.406]
std  = [0.229, 0.224, 0.225]
```

Bunun sebebi ResNet, EfficientNet ve Xception gibi modellerin ImageNet üzerinde ön eğitimli olmasıdır. Modelin beklediği giriş dağılımına yakın görüntü verilmiş olur.

---

## 4. Canlı Sistemde Yüz Kırpma

Web demo kısmında kullanıcı rastgele bir fotoğraf yüklediğinde sistem önce yüzü bulmaya çalışır.

Kullanılan yöntem:

- OpenCV Haar Cascade yüz algılama
- Göz tespiti ile aday yüz doğrulama
- En büyük yüz bölgesinin seçilmesi
- Yüz kutusunun %35 margin ile genişletilmesi
- Modelin tüm fotoğraf yerine yüz bölgesine odaklanması

Akış:

```text
Yüklenen görsel
   ↓
Yüz tespiti
   ↓
En büyük yüzü kırp
   ↓
224x224 resize + normalization
   ↓
Model tahmini
```

Bu önemlidir çünkü internetten gelen fotoğraflarda arka plan, kıyafet, ışık veya kompozisyon modeli yanıltabilir. Yüz kırpma, modeli asıl karar bölgesine yaklaştırır.

---

## 5. Kullanılan Modeller

Projede karşılaştırılan ana modeller:

| Model | Açıklama |
|---|---|
| MesoNet | Deepfake tespitine özel hafif CNN |
| ResNet-50 | ImageNet ön eğitimli güçlü CNN |
| EfficientNet-B4 | Parametre/verimlilik dengesi güçlü model |
| Xception | Derin ayrıştırılabilir konvolüsyon kullanan güçlü CNN |
| Xception + DF40 | Dış veriyle yeniden eğitilmiş final model |

Kodda ViT desteği de vardır, ancak final demo ve ana karşılaştırmada odak CNN modellerindedir.

---

## 6. MesoNet Mimarisi

MesoNet sıfırdan yazılmıştır. Hafif bir CNN mimarisidir.

Giriş:

```text
3 x 224 x 224 RGB görüntü
```

Mimari:

```text
Conv2D 3→8
BatchNorm
ReLU
MaxPool

Conv2D 8→8
BatchNorm
ReLU
MaxPool

Conv2D 8→16
BatchNorm
ReLU
MaxPool

Conv2D 16→16
BatchNorm
ReLU
MaxPool

Flatten
Dropout
Linear 16*7*7 → 16
LeakyReLU
Dropout
Linear 16 → 2
```

Avantajı: çok hafif ve hızlıdır.

Dezavantajı: karmaşık deepfake izlerini yakalamada daha güçlü modellere göre zayıf kalır.

---

## 7. Transfer Learning Yaklaşımı

ResNet-50, EfficientNet-B4 ve Xception modellerinde transfer learning kullanılmıştır.

Yani modeller ImageNet üzerinde önceden eğitilmiş ağırlıklarla başlatılmıştır. Son sınıflandırma katmanı iki sınıfa göre değiştirilmiştir:

```text
real
fake
```

Bunun avantajı:

- Daha hızlı yakınsama
- Daha az veriyle daha iyi başlangıç
- Görsel özellik çıkarma kabiliyetinin hazır gelmesi

---

## 8. Eğitim Ayarları

Genel ayarlar:

```text
image_size = 224
seed = 42
device = cuda varsa cuda, yoksa cpu
mixed_precision = true
num_workers = 4
pin_memory = true
```

Loss fonksiyonu:

```text
CrossEntropyLoss(label_smoothing=0.1)
```

Label smoothing, modelin aşırı emin olmasını azaltır ve genelleme kabiliyetine katkı sağlayabilir.

Optimizer:

```text
AdamW
```

Scheduler:

```text
CosineAnnealingLR
```

Gradient clipping:

```text
max_norm = 1.0
```

Early stopping:

```text
validation loss iyileşmezse 5 epoch sonra durdur
```

Checkpoint mantığı:

```text
En düşük validation loss görüldüğünde model kaydedilir.
```

---

## 9. Model Bazlı Hiperparametreler

| Model | Batch | LR | Epoch | Weight Decay |
|---|---:|---:|---:|---:|
| MesoNet | 64 | 1e-3 | 20 | 1e-4 |
| ResNet-50 | 32 | 1e-4 | 20 | 1e-4 |
| EfficientNet-B4 | 16 | 5e-5 | 20 | 1e-4 |
| Xception | 16 | 5e-5 | 20 | 1e-4 |
| Xception + DF40 | 16 | 5e-5 | 8 | 1e-4 |

Colab tarafında final model Tesla T4 üzerinde mixed precision ile eğitilmiştir.

---

## 10. Değerlendirme Metrikleri

Kullanılan metrikler:

### Accuracy

Genel doğru tahmin oranıdır.

```text
Accuracy = doğru tahmin / toplam örnek
```

### Precision

Modelin fake dediği örneklerin ne kadarının gerçekten fake olduğunu gösterir.

```text
Precision = TP / (TP + FP)
```

### Recall

Gerçek fake örneklerin ne kadarını yakaladığını gösterir.

```text
Recall = TP / (TP + FN)
```

Deepfake tespitinde özellikle önemlidir çünkü fake örneği gerçek sanmak kritik hatadır.

### F1-score

Precision ve recall’un dengeli ortalamasıdır.

```text
F1 = 2 * precision * recall / (precision + recall)
```

### AUC-ROC

Modelin farklı eşik değerlerinde real/fake ayrım gücünü ölçer. Accuracy’den daha genel bir ayrım performansı verir.

### Confusion Matrix

Bu projede sınıf sırası:

```text
real = 0
fake = 1
```

Matris yapısı:

```text
[ [real doğru, real → fake hatası],
  [fake → real hatası, fake doğru] ]
```

---

## 11. Ana Veri Seti Sonuçları

| Model | Accuracy | AUC | F1 | Precision | Recall | Boyut |
|---|---:|---:|---:|---:|---:|---:|
| MesoNet | %81.34 | 0.9067 | 0.7930 | 0.8900 | 0.7151 | 0.09 MB |
| ResNet-50 | %97.31 | 0.9990 | 0.9724 | 0.9987 | 0.9475 | 89.89 MB |
| EfficientNet-B4 | %99.60 | 0.9999 | 0.9960 | 0.9988 | 0.9932 | 67.43 MB |
| Xception | %99.73 | 0.9994 | 0.9973 | 0.9977 | 0.9970 | 79.60 MB |
| Xception + DF40 | %99.10 | 0.9989 | 0.9910 | 0.9857 | 0.9965 | 79.60 MB |

Ana veri setinde en yüksek accuracy eski Xception’da çıkmıştır. Ancak bu tek başına final seçim için yeterli görülmemiştir.

---

## 12. En Kritik Bulgu: Dış Veri Testi

Eski Xception ana testte çok başarılıydı:

```text
Ana test accuracy: %99.73
```

Fakat dış testte:

```text
Accuracy: %52.74
AUC: 0.6141
Fake recall: %6.04
```

Bu çok önemlidir. Çünkü fake recall %6.04 demek, dış veri setindeki fake görüntülerin neredeyse tamamını kaçırmak demektir.

Yeni Xception + DF40 modeli dış testte:

```text
Accuracy: %92.15
AUC: 0.9828
Fake recall: %84.50
Precision: %99.78 civarı
```

Bu, projenin ana katkısıdır.

Raporda bunu şöyle anlatabilirsin:

> İlk model, aynı veri dağılımında yüksek doğruluk elde etmesine rağmen dış veri setinde ciddi performans kaybı yaşamıştır. Bu durum modelin veri setine özgü örüntüleri öğrenmiş olabileceğini göstermektedir. Dış veri eklenerek yeniden eğitilen Xception modeli, orijinal test setinde küçük bir doğruluk kaybı yaşasa da dış test setinde belirgin bir iyileşme sağlamıştır. Bu sonuç, veri çeşitliliğinin deepfake tespitinde genelleme başarımı için kritik olduğunu göstermektedir.

---

## 13. Neden Final Model Xception + DF40?

Çünkü amaç sadece ana test setinde en yüksek skoru almak değildir.

Eski Xception:

```text
Ana test: çok iyi
Dış test: zayıf
```

Yeni Xception + DF40:

```text
Ana test: hâlâ çok iyi
Dış test: çok daha güçlü
```

Yani final model daha dengeli ve gerçek kullanım senaryosuna daha yakındır.

Jüriye şöyle söylenebilir:

> Eski Xception kapalı veri dağılımında daha yüksek accuracy verse de dış veri setinde genelleme başarımı düşüktü. Final modelde küçük bir in-domain kayıp karşılığında büyük bir out-of-domain kazanım elde edildi. Bu yüzden nihai model olarak Xception + DF40 seçildi.

---

## 14. Eğitim Analizi Nasıl Yorumlanır?

Eğitim grafiklerinde iki ana şey vardır:

### Loss grafiği

Train loss ve validation loss zamanla azalırsa model öğreniyor demektir.

Ama train loss düşüp validation loss yükselirse overfitting olabilir.

### Accuracy grafiği

Train accuracy ve validation accuracy birlikte yükselirse model hem öğreniyor hem genelliyor demektir.

Final model için önemli yorum:

> Dış veri eklendikten sonra modelin validation başarımı yüksek seviyede kalmıştır. Bu durum modelin yalnızca ana veri setini ezberlemek yerine daha çeşitli örüntülerden öğrenme yaptığını gösterir.

---

## 15. Web Uygulaması Mimarisi

Sistem iki parçalıdır:

```text
React + Vite Frontend
        ↓ HTTP API
Flask Backend
        ↓
PyTorch Model
```

### Backend

Dosya:

```text
web/server.py
```

Ana endpointler:

| Endpoint | Görev |
|---|---|
| `/api/models` | Eğitilmiş modelleri listeler |
| `/api/predict` | Seçilen tek modelle tahmin yapar |
| `/api/predict-all` | Tüm modellerle aynı görseli test eder |
| `/api/metrics` | Model metriklerini frontend’e verir |
| `/api/logs` | Eğitim geçmişini verir |
| `/api/plots/<filename>` | Grafik dosyalarını servis eder |

Tahmin akışı:

```text
Kullanıcı görsel yükler
   ↓
Flask görseli alır
   ↓
PIL ile RGB’ye çevirir
   ↓
Yüz kırpma uygular
   ↓
224x224 + normalization
   ↓
Model forward pass
   ↓
Softmax
   ↓
real_probability / fake_probability
   ↓
JSON response
```

### Frontend

React arayüzünde üç ana bölüm vardır:

1. **Canlı Analiz**
   - Görsel yükleme
   - Model seçme
   - Real/fake sonucu
   - Güven seviyesi
   - Fake olasılığı
   - Yüz kırpma önizlemesi

2. **Model Karşılaştırma**
   - Accuracy
   - AUC
   - F1
   - Çıkarım süresi
   - Model bazlı tablo

3. **Eğitim Analizi**
   - Loss eğrileri
   - Accuracy eğrileri
   - ROC curve
   - Confusion matrix

---

## 16. Colab Kullanımının Teknik Nedeni

Yerel bilgisayarda eğitim uzun sürdü çünkü:

- Veri seti büyük
- Xception/EfficientNet gibi modeller ağır
- GPU belleği sınırlı
- Epoch süreleri uzundu
- Disk alanı problemi vardı

Colab Pro ile:

- Tesla T4 GPU kullanıldı
- CUDA aktif çalıştı
- Mixed precision ile eğitim hızlandı
- Büyük veri setleri Drive üzerinden taşındı
- Checkpoint alınarak eğitim kesilip devam ettirildi

Akademik olarak şöyle yazılabilir:

> Model eğitim sürelerini azaltmak ve GPU bellek kısıtlarını aşmak amacıyla Google Colab Pro ortamından yararlanılmıştır. Eğitim sırasında CUDA destekli GPU ve mixed precision kullanılmıştır.

---

## 17. Projenin Güçlü Yönleri

- Birden fazla model karşılaştırılmıştır.
- Sadece accuracy değil AUC, F1, precision, recall da hesaplanmıştır.
- Eğitim grafikleri ve confusion matrix üretilmiştir.
- Web demo ile model pratik kullanıma dönüştürülmüştür.
- Dış veri testiyle gerçek genelleme problemi gösterilmiştir.
- Final model bu probleme göre iyileştirilmiştir.
- Eski ve yeni model arasındaki fark somut olarak gösterilmiştir.

---

## 18. Projenin Sınırlılıkları

Bunları saklamak yerine akademik olarak söylemek projeyi daha güçlü gösterir.

- Sistem video değil, görüntü tabanlı çalışır.
- Yüz tespiti Haar Cascade kullandığı için yan profil, düşük ışık veya kapalı yüzlerde hata yapabilir.
- Deepfake üretim teknikleri sürekli değiştiği için model düzenli olarak yeni veriyle güncellenmelidir.
- Ana veri setinde yüksek başarı, gerçek dünya başarısını garanti etmez.
- Model açıklanabilirliği sınırlıdır; kararın hangi piksel izlerinden geldiği ayrıca Grad-CAM gibi yöntemlerle güçlendirilebilir.

---

## 19. Jüri Sorarsa Kısa Cevaplar

### Neden Xception seçildi?

Çünkü ana veri setinde en yüksek başarıyı verdi ve dış veriyle yeniden eğitildiğinde genelleme performansı ciddi şekilde arttı.

### Eski model %99 iken neden yeni modele geçtiniz?

Çünkü %99 başarı aynı veri dağılımı içindi. Dış veri testinde eski model %52’ye düştü. Yeni model dış testte %92’ye çıktı.

### Accuracy yeterli değil mi?

Hayır. Deepfake tespitinde recall ve AUC de önemlidir. Özellikle fake örnekleri kaçırmak kritik olduğu için fake recall ayrıca incelendi.

### Model overfit oldu mu?

İlk modelin dış veride başarısız olması dağılım bağımlılığına işaret ediyordu. Dış veri eklenerek modelin daha çeşitli örüntüler öğrenmesi sağlandı.

### Face crop neden var?

Çünkü modelin arka plan yerine yüz bölgesine odaklanması isteniyor. İnternetten gelen görüntülerde yüz dışı alanlar yanıltıcı olabilir.

### Bu sistem gerçek dünyada kullanılabilir mi?

Temel bir prototip olarak kullanılabilir; ancak üretim seviyesinde daha büyük ve güncel veri setleri, video tabanlı analiz, açıklanabilirlik ve güvenlik testleri gerekir.

---

## 20. Tek Cümlelik Akademik Katkı

Rapor veya video için kullanılabilecek kısa katkı cümlesi:

> Bu çalışmanın temel katkısı, deepfake görüntü tespitinde farklı derin öğrenme mimarilerini karşılaştırmak ve yalnızca kapalı veri seti başarımına değil, dış veri setlerinde genelleme performansına da odaklanan daha dayanıklı bir Xception tabanlı model geliştirmektir.
