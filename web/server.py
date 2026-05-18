import sys
import time
from pathlib import Path

# Proje ana dizinini sys.path'e ekleyelim ki imports düzgün çalışsın
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import torch
import io
import json
import os
import base64

from models.model_factory import get_model, MODEL_DISPLAY_NAMES
from preprocessing.face_crop import crop_largest_face
from training.config import CHECKPOINTS_DIR, DEMO_MODELS, IDX_TO_CLASS
from torchvision import transforms

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get("MAX_UPLOAD_MB", "10")) * 1024 * 1024

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS(app, resources={r"/api/*": {"origins": [origin.strip() for origin in cors_origins.split(",") if origin.strip()]}})

AVAILABLE_MODELS = DEMO_MODELS
FACE_CROP_ENABLED = os.environ.get("FACE_CROP_ENABLED", "1") == "1"

def get_trained_models():
    return [m for m in AVAILABLE_MODELS if (CHECKPOINTS_DIR / f"{m}_best.pth").exists()]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
loaded_models = {}
predict_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def load_cached_model(model_name):
    if model_name not in AVAILABLE_MODELS:
        return None

    if model_name in loaded_models:
        return loaded_models[model_name]
    
    ckpt = CHECKPOINTS_DIR / f"{model_name}_best.pth"
    if not ckpt.exists():
        return None
    
    model = get_model(model_name).to(device)
    state = torch.load(ckpt, map_location=device, weights_only=True)
    model.load_state_dict(state["model_state_dict"])
    model.eval()
    
    loaded_models[model_name] = model
    return model

def preprocess_image(image):
    if not FACE_CROP_ENABLED:
        return image, {
            'enabled': False,
            'applied': False,
            'box': None,
            'original_size': [int(value) for value in image.size],
            'cropped_size': [int(value) for value in image.size],
            'detected_count': 0,
            'rejected_count': 0,
            'reason': 'face_crop_disabled',
        }

    crop = crop_largest_face(image)
    buffer = io.BytesIO()
    crop.image.save(buffer, format="JPEG", quality=92)
    preview_url = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    return crop.image, {
        'enabled': True,
        'applied': bool(crop.applied),
        'box': [int(value) for value in crop.box] if crop.box else None,
        'original_size': [int(value) for value in crop.original_size],
        'cropped_size': [int(value) for value in crop.cropped_size],
        'detected_count': int(crop.detected_count),
        'rejected_count': int(crop.rejected_count),
        'reason': crop.reason,
        'preview_url': preview_url,
    }

# SUNUM-ANAHTAR: web demo inference - yuklenen tek gorsel icin model tahmini burada calisir.
def run_prediction(model_name, image):
    model = load_cached_model(model_name)
    if model is None:
        return None

    tensor = predict_transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()

        out = model(tensor)

        if device.type == "cuda":
            torch.cuda.synchronize()
        ms = (time.perf_counter() - t0) * 1000

        probs = torch.softmax(out, dim=1).squeeze()
        pred_idx = probs.argmax().item()
        label = IDX_TO_CLASS[pred_idx]
        confidence = probs[pred_idx].item()

    return {
        'model': model_name,
        'display_name': MODEL_DISPLAY_NAMES.get(model_name, model_name),
        'label': label,
        'confidence': confidence,
        'real_probability': probs[0].item(),
        'fake_probability': probs[1].item(),
        'inference_time_ms': round(ms, 2)
    }

@app.route('/')
def index():
    return jsonify({"status": "DeepFakeBusted API is running", "available_models": get_trained_models()})

# SUNUM-ANAHTAR: API predict - secilen tek modelle canli tahmin endpoint'i.
@app.route('/api/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'Resim yüklenmedi.'}), 400
        
    model_name = request.form.get('model')
    if not model_name:
        return jsonify({'error': 'Model seçilmedi.'}), 400
    if model_name not in AVAILABLE_MODELS:
        return jsonify({'error': 'Geçersiz model seçimi.'}), 400
        
    file = request.files['image']
    try:
        image = Image.open(file.stream).convert("RGB")
    except Exception as e:
        return jsonify({'error': 'Geçersiz resim formatı.'}), 400

    image, face_crop = preprocess_image(image)
    result = run_prediction(model_name, image)
    if result is None:
        return jsonify({'error': 'Model bulunamadı veya henüz eğitilmemiş.'}), 404

    result['face_crop'] = face_crop
    return jsonify(result)

# SUNUM-ANAHTAR: all models comparison - tek tusla tum egitilmis modelleri yan yana test eden endpoint.
@app.route('/api/predict-all', methods=['POST'])
def predict_all():
    if 'image' not in request.files:
        return jsonify({'error': 'Resim yüklenmedi.'}), 400

    file = request.files['image']
    try:
        image = Image.open(file.stream).convert("RGB")
    except Exception:
        return jsonify({'error': 'Geçersiz resim formatı.'}), 400

    image, face_crop = preprocess_image(image)
    trained_models = get_trained_models()
    if not trained_models:
        return jsonify({'error': 'Eğitilmiş model bulunamadı.'}), 404

    results = []
    for model_name in trained_models:
        result = run_prediction(model_name, image)
        if result is not None:
            results.append(result)

    fake_votes = sum(1 for item in results if item['label'] == 'fake')
    real_votes = len(results) - fake_votes
    avg_fake_probability = sum(item['fake_probability'] for item in results) / len(results)
    consensus_label = 'fake' if fake_votes > real_votes else 'real'

    return jsonify({
        'results': results,
        'summary': {
            'model_count': len(results),
            'fake_votes': fake_votes,
            'real_votes': real_votes,
            'avg_fake_probability': avg_fake_probability,
            'consensus_label': consensus_label,
            'face_crop': face_crop,
        }
    })

# SUNUM-ANAHTAR: metrics API - web arayuzune model karsilastirma metriklerini verir.
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    metrics_data = {}
    metrics_dir = Path(__file__).parent.parent / "results" / "metrics"
    if metrics_dir.exists():
        for f in metrics_dir.glob("*_metrics.json"):
            model_name = f.stem.replace("_metrics", "")
            with open(f, 'r', encoding='utf-8') as file:
                metrics_data[model_name] = json.load(file)
    return jsonify(metrics_data)

@app.route('/api/logs', methods=['GET'])
def get_logs():
    logs_data = {}
    logs_dir = Path(__file__).parent.parent / "results" / "logs"
    if logs_dir.exists():
        for f in logs_dir.glob("*_training.json"):
            model_name = f.stem.replace("_training", "")
            with open(f, 'r', encoding='utf-8') as file:
                logs_data[model_name] = json.load(file)
    return jsonify(logs_data)

@app.route('/api/plots/<path:filename>')
def serve_plots(filename):
    plots_dir = Path(__file__).parent.parent / "results" / "plots"
    return send_from_directory(plots_dir, filename)

@app.route('/api/models', methods=['GET'])
def get_models_info():
    return jsonify({"models": get_trained_models(), "display_names": MODEL_DISPLAY_NAMES})

@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({'error': 'Dosya çok büyük. Daha küçük bir resim yükleyin.'}), 413

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Unexpected API error")
    return jsonify({'error': f'Beklenmeyen sunucu hatası: {error}'}), 500

if __name__ == '__main__':
    print(f"Sunucu başlatılıyor... Device: {device}")
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
