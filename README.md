# DeepFakeBusted 🕵️

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-EE4C2C?logo=pytorch&logoColor=white)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?logo=react&logoColor=black)
![Task](https://img.shields.io/badge/Task-Deepfake%20Detection-111827)

**DeepFakeBusted** is a deep learning-based deepfake image detection system that compares multiple CNN architectures and improves cross-dataset generalization with an enhanced Xception model.  
**DeepFakeBusted**, farklı CNN mimarilerini karşılaştıran ve geliştirilmiş Xception modeliyle farklı veri kümelerinde genelleme başarımını artıran derin öğrenme tabanlı bir deepfake görüntü tespit sistemidir.

---

## Project at a Glance

| Başlık | Sonuç |
|---|---|
| Karşılaştırılan modeller | MesoNet, ResNet-50, EfficientNet-B4, Xception |
| En yüksek orijinal test başarımı | **Xception — %99.73 accuracy** |
| Dağılım değişimindeki problem | Eski Xception dış testte yalnızca **%52.74 accuracy** ve **%6.04 fake recall** |
| Nihai tercih edilen model | **Xception + DF40 Dış Veri** |
| Nihai dış test başarımı | **%92.15 accuracy**, **0.9828 AUC**, **%84.50 fake recall** |
| Uygulama katmanı | Flask API + React/Vite web arayüzü |

Bu proje, kapalı dağılımdaki yüksek doğruluğun tek başına yeterli olmadığını; gerçek dünyaya daha yakın senaryolarda veri çeşitliliğinin kritik olduğunu gösterir.

---

## Demo

![DeepFakeBusted training analysis](results/plots/ui_analysis_final.png)

Web arayüzü şunları sunar:

- Tek görsel üzerinde canlı deepfake analizi
- Yüz kırpma tabanlı ön işleme
- Tüm modellerle karşılaştırmalı tahmin
- Accuracy, AUC, F1 ve çıkarım süresi tablosu
- Eğitim kaybı / doğruluk eğrileri ve ROC / confusion matrix grafikleri

---

## En Önemli Bulgular

### 1. Aynı veri dağılımında çok yüksek başarı

| Model | Accuracy | AUC-ROC | F1-Score |
|---|---:|---:|---:|
| MesoNet | %81.34 | 0.9067 | 0.7930 |
| ResNet-50 | %97.31 | 0.9990 | 0.9724 |
| EfficientNet-B4 | %99.60 | 0.9999 | 0.9960 |
| **Xception** | **%99.73** | **0.9994** | **0.9973** |

### 2. Dış veri geldiğinde tablo değişiyor

| Model | Orijinal test accuracy | Dış test accuracy | Dış test fake recall |
|---|---:|---:|---:|
| Xception | %99.73 | %52.74 | %6.04 |
| **Xception + DF40 Dış Veri** | **%99.10** | **%92.15** | **%84.50** |

Yeni model, orijinal test setinde çok küçük bir kayıp yaşarken dış veri setinde dramatik biçimde güçlendi. Projenin asıl katkısı da burada: yalnızca “yüksek skor” üretmek yerine, modelin görülmemiş deepfake örneklerine daha dayanıklı hale gelmesini sağlamak.

---

## Kullanılan Teknolojiler

- **Python, PyTorch, torchvision, timm**
- **Flask** tabanlı backend API
- **React + Vite** tabanlı frontend
- Eğitim ve değerlendirme için:
  - Accuracy
  - AUC-ROC
  - F1-Score
  - Precision / Recall
  - Inference time
  - Confusion matrix / ROC curve

---

## Proje Yapısı

```text
DeepFakeBusted/
├── colab/                    # Google Colab çalışma defteri
├── models/                   # Model tanımları ve factory
├── preprocessing/            # Yüz kırpma işlemleri
├── training/                 # Eğitim, değerlendirme ve ayarlar
├── scripts/                  # Veri hazırlama ve yardımcı scriptler
├── results/
│   ├── logs/                 # Eğitim logları
│   ├── metrics/              # Ölçüm çıktıları
│   └── plots/                # Grafikler
├── web/
│   ├── server.py             # Flask API
│   └── frontend/             # React arayüzü
└── requirements.txt
```

> Not: Veri setleri, sanal ortam dosyaları ve eğitim checkpoint'leri repo boyutunu makul tutmak için GitHub'a eklenmemiştir.

---

## Kurulum

```bash
# 1. Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. CUDA destekli PyTorch kurulumu
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

---

## Veri Setleri

### Ana veri seti

**140k Real and Fake Faces**  
https://www.kaggle.com/datasets/xhlulu/140k-real-and-fake-faces

```bash
pip install kaggle
kaggle datasets download -d xhlulu/140k-real-and-fake-faces -p data/raw/ --unzip
python scripts/prepare_data.py --source data/raw/real-vs-fake --dest data/processed
```

### Dış veri seti

Genelleme çalışması için DF40 tabanlı ek dış veri kullanılmıştır. Bu veri, `train / val / test` ayrımıyla ikinci bir veri kökü olarak eğitime dahil edilmiştir.

---

## Eğitim

```bash
# Temel modeller
python -m training.train --model mesonet
python -m training.train --model resnet50
python -m training.train --model efficientnet_b4
python -m training.train --model xception

# Dış veri ile genelleme odaklı Xception eğitimi
python -m training.train --model xception \
  --extra-data-dir path/to/external_dataset \
  --run-name xception_hfdf40
```

Google Colab akışı için hazır notebook:  
`colab/DeepFakeBusted_Pro_Run.ipynb`

---

## Değerlendirme

```bash
# Tek model
python -m training.evaluate --model xception

# Tüm temel modeller
python -m training.evaluate --model all

# Dış veriyle eğitilmiş modeli değerlendirme
python -m training.evaluate --model xception \
  --run-name xception_hfdf40 \
  --extra-data-dir path/to/external_dataset
```

Çıktılar:

- `results/metrics/`
- `results/plots/`

---

## Web Demo

```bash
# Backend
python web/server.py

# Frontend
cd web/frontend
npm install
npm run dev
```

Frontend varsayılan olarak `http://127.0.0.1:5000/api` adresindeki API'ye bağlanır.

---

## Modeller

| Model | Açıklama |
|---|---|
| **MesoNet** | Deepfake tespiti için hafif CNN |
| **ResNet-50** | Güçlü transfer learning baseline |
| **EfficientNet-B4** | Yüksek doğruluk / verimlilik dengesi |
| **Xception** | Projede en yüksek kapalı dağılım başarımı |
| **Xception + DF40 Dış Veri** | Daha güçlü cross-dataset genelleme için nihai model |

---

## Referanslar

- Afchar et al. (2018). *MesoNet: a Compact Facial Video Forgery Detection Network.*
- Rössler et al. (2019). *FaceForensics++: Learning to Detect Manipulated Facial Images.*
- Tan & Le (2019). *EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks.*
- Dosovitskiy et al. (2020). *An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale.*

