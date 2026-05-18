# DeepFakeBusted 🕵️

Deepfake görüntü algılama alanında birden fazla derin öğrenme modelini karşılaştıran bitirme projesi.

---

## Proje Yapısı

```text
DeepFakeBusted/
├── data/
│   ├── raw/                  # Kaggle'dan indirilen ham veri
│   └── processed/            # Hazırlanmış train/valid/test
├── models/
│   ├── mesonet.py            # MesoNet (Meso4) — sıfırdan yazıldı
│   └── model_factory.py      # Tüm modeller için factory
├── training/
│   ├── config.py             # Hiperparametreler, path'ler
│   ├── dataset.py            # Custom Dataset + DataLoader
│   ├── train.py              # Eğitim döngüsü
│   └── evaluate.py           # Metrik hesaplama + grafikler
├── scripts/
│   └── prepare_data.py       # Kaggle veri setini hazırlama
├── results/                  # Otomatik oluşturulur
│   ├── checkpoints/          # .pth model ağırlıkları
│   ├── logs/                 # Eğitim JSON logları
│   ├── metrics/              # Değerlendirme JSON sonuçları
│   └── plots/                # Confusion matrix, ROC grafikleri
├── web/
│   ├── server.py             # Flask API
│   └── frontend/             # React + Vite web arayüzü
└── requirements.txt
```

---

## Kurulum

```bash
# 1. Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate          # Windows

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. PyTorch + CUDA (RTX 3050 Ti için CUDA 12.x)
#    https://pytorch.org/get-started/locally/
# Örnek:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

---

## Veri Seti

**140k Real and Fake Faces** (Kaggle):  
<https://www.kaggle.com/datasets/xhlulu/140k-real-and-fake-faces>

```bash
# Kaggle API ile indir
pip install kaggle
# kaggle.json dosyasını ~/.kaggle/ altına koy
kaggle datasets download -d xhlulu/140k-real-and-fake-faces -p data/raw/ --unzip
```

Veri setini hazırla:

```bash
python scripts/prepare_data.py --source data/raw/real-vs-fake --dest data/processed
```

**Hızlı test için** (ilk 5000 görüntü/class):

```bash
python scripts/prepare_data.py --source data/raw/real-vs-fake --dest data/processed --max-per-class 5000
```

Eğitim varsayılan olarak Kaggle arşivinin hazır `train/valid/test` yapısını kullanır. Hazırlanmış klasörü kullanmak için:

```bash
python -m training.train --model mesonet --data-dir data/processed
python -m training.evaluate --model mesonet --data-dir data/processed
```

---

## Eğitim

```bash
# Tek model
python -m training.train --model mesonet
python -m training.train --model resnet50
python -m training.train --model efficientnet_b4

# Sırayla tümünü eğit (gece bırak)
python -m training.train --model mesonet && ^
python -m training.train --model resnet50 && ^
python -m training.train --model efficientnet_b4
```

Model ağırlıkları → `results/checkpoints/{model}_best.pth`  
Eğitim logları → `results/logs/{model}_training.json`

---

## Değerlendirme

```bash
python -m training.evaluate --model resnet50
python -m training.evaluate --model all        # tüm eğitilmiş modeller
```

Metrikler → `results/metrics/`  
Grafikler → `results/plots/`

---

## Web Demo

```bash
# 1. API
python web/server.py

# 2. Frontend (ayrı terminal)
cd web/frontend
npm install
npm run dev
```

Tarayıcıda Vite'ın yazdırdığı adresi açın. Varsayılan frontend `http://127.0.0.1:5000/api` API'sine bağlanır.

**Demo özellikleri:**
- 🏠 Ana Sayfa — proje açıklaması
- 🔬 Canlı Tahmin — görüntü yükle, model seç, sonucu gör
- 📊 Model Karşılaştırması — metrik tablosu + ROC + confusion matrix
- 📈 Eğitim Geçmişi — loss/accuracy eğrileri

---

## Karşılaştırılan Modeller

| Model | Kaynak | Açıklama |
|---|---|---|
| **MesoNet** | Sıfırdan yazıldı | Deepfake'e özel hafif CNN |
| **ResNet-50** | torchvision pretrained | Güçlü baseline |
| **EfficientNet-B4** | timm pretrained | Yüksek performans |
| **Xception** | timm pretrained | FF++ referans model |
| **Xception + DF40 Dış Veri** | timm pretrained | Dış veri ile yeniden eğitilmiş genelleme odaklı model |
| **ViT-B/16** | timm pretrained | Transformer yaklaşımı |

---

## Değerlendirme Metrikleri

- Accuracy, AUC-ROC, F1-Score, Precision, Recall
- Inference Time (ms / görüntü)
- Model Boyutu (MB)

---

## Son Geliştirme: Dış Veri ile Genelleme

Orijinal Xception modeli aynı dağılımdan gelen test setinde çok yüksek başarı gösterirken, farklı dağılımdan gelen dış test verisinde belirgin performans kaybı yaşadı. Bu nedenle DF40 tabanlı dış veri ile yeniden eğitilen ikinci bir Xception varyantı geliştirildi.

| Model | Orijinal test accuracy | Dış test accuracy | Dış test fake recall |
|---|---:|---:|---:|
| Xception | 99.73% | 52.74% | 6.04% |
| Xception + DF40 Dış Veri | 99.10% | 92.15% | 84.50% |

Bu sonuçlar, kapalı dağılımdaki çok yüksek başarının tek başına yeterli olmadığını; veri çeşitliliğinin görülmemiş deepfake türlerine genelleme için kritik olduğunu gösterir.

---

## Referanslar

- Afchar et al. (2018). *MesoNet: a Compact Facial Video Forgery Detection Network.* <https://arxiv.org/abs/1809.00888>
- Rossler et al. (2019). *FaceForensics++*. <https://arxiv.org/abs/1901.08971>
- Tan & Le (2019). *EfficientNet.* <https://arxiv.org/abs/1905.11946>
- Dosovitskiy et al. (2020). *An Image is Worth 16x16 Words.* <https://arxiv.org/abs/2010.11929>
