# Nihai Xception Karşılaştırması

| Model | Orijinal test accuracy | Orijinal test AUC | Dış test accuracy | Dış test AUC | Dış test fake recall |
|---|---:|---:|---:|---:|---:|
| Eski Xception | %99.73 | 0.9994 | %52.74 | 0.6141 | %6.04 |
| Yeni Xception + DF40 dış veri | %99.10 | 0.9989 | %92.15 | 0.9828 | %84.50 |

## Kısa yorum

Yeni model, orijinal test setinde küçük bir kayıp yaşasa da dış veri setinde çok büyük bir kazanım sağladı. Bu fark, modelin yalnızca eğitim dağılımını ezberlemek yerine daha genel deepfake izlerini öğrenmeye başladığını gösteriyor.
