"""
LifeLine Enterprise Machine Learning & Resource Optimization Microservice
Integrates trained CrisisMMD v2.0 NLP & PyTorch MobileNetV3 Vision Models for:
1. Real vs Fake / Off-Topic Image Authenticity Filtering.
2. Visual Disaster Damage Severity Scoring (Severe, Mild, Little/None).
3. Humanitarian NLP Triage & SciPy MILP Resource Allocation.
Listens on: http://127.0.0.1:5000
"""

from flask import Flask, request, jsonify
import math, os, sys, re, pickle
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)

# Device setup
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 1. Load CrisisMMD NLP Model & Vectorizer
CRISISMMD_MODEL_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_model.pkl"
CRISISMMD_VEC_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_vectorizer.pkl"

crisismmd_model = None
crisismmd_vectorizer = None

try:
    if os.path.exists(CRISISMMD_MODEL_PATH) and os.path.exists(CRISISMMD_VEC_PATH):
        with open(CRISISMMD_MODEL_PATH, 'rb') as f:
            crisismmd_model = pickle.load(f)
        with open(CRISISMMD_VEC_PATH, 'rb') as f:
            crisismmd_vectorizer = pickle.load(f)
        print("✅ [ML Microservice] CrisisMMD v2.0 NLP Model & Vectorizer loaded!")
except Exception as e:
    print(f"⚠️ [ML Microservice] Error loading CrisisMMD NLP model: {e}")

# 2. Load CrisisMMD PyTorch Vision Models (Authenticity & Damage Severity)
AUTH_WEIGHTS_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_vision_authenticity.pt"
DMG_WEIGHTS_PATH = r"c:\Users\Vijay\LifeLine\crisismmd_vision_damage.pt"

auth_vision_model = None
dmg_vision_model = None

try:
    # Authenticity Model (2 Classes: Informative/Real vs Not_Informative/Fake)
    auth_m = models.mobilenet_v3_small(weights=None)
    auth_m.classifier[3] = nn.Linear(auth_m.classifier[3].in_features, 2)
    if os.path.exists(AUTH_WEIGHTS_PATH):
        auth_m.load_state_dict(torch.load(AUTH_WEIGHTS_PATH, map_location=device))
        auth_m.eval()
        auth_vision_model = auth_m.to(device)
        print("✅ [ML Microservice] CrisisMMD PyTorch Image Authenticity Model loaded!")
    
    # Damage Severity Model (3 Classes: Little/No, Mild, Severe)
    dmg_m = models.mobilenet_v3_small(weights=None)
    dmg_m.classifier[3] = nn.Linear(dmg_m.classifier[3].in_features, 3)
    if os.path.exists(DMG_WEIGHTS_PATH):
        dmg_m.load_state_dict(torch.load(DMG_WEIGHTS_PATH, map_location=device))
        dmg_m.eval()
        dmg_vision_model = dmg_m.to(device)
        print("✅ [ML Microservice] CrisisMMD PyTorch Damage Severity Model loaded!")
except Exception as e:
    print(f"⚠️ [ML Microservice] Error loading CrisisMMD Vision models: {e}")

# Image Transform
vision_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_text_entropy(text):
    if not text: return 0
    prob = [float(text.count(c)) / len(text) for c in set(text)]
    return - sum([p * math.log(p) / math.log(2.0) for p in prob])

def detect_fake_or_gibberish(text):
    text_clean = text.strip().lower()
    if len(text_clean) < 5:
        return True, "Description under 5 characters"
    if len(set(text_clean)) <= 3 and len(text_clean) > 8:
        return True, "Repeated single character spam"
    words = re.findall(r'\w+', text_clean)
    avg_word_len = sum(len(w) for w in words) / max(1, len(words))
    if avg_word_len > 14 and len(words) < 3:
        return True, "Keyboard mashing / gibberish text detected"
    return False, None

# 1. NLP Text Classification Endpoint
@app.route('/predict/text', methods=['POST'])
def predict_text():
    data = request.json or {}
    text = data.get('text', '').lower()

    is_fake, fake_reason = detect_fake_or_gibberish(text)
    if is_fake:
        return jsonify({
            'category': 'Unverified',
            'text_severity': 1.0,
            'confidence': 0.10,
            'is_fake': True,
            'fake_reason': fake_reason,
            'model_source': 'Anti-Fake Pre-Filter'
        })

    category = "General Disaster Alert"
    confidence = 0.85

    if crisismmd_model and crisismmd_vectorizer:
        try:
            vec = crisismmd_vectorizer.transform([text])
            pred_cat = crisismmd_model.predict(vec)[0]
            probs = crisismmd_model.predict_proba(vec)[0]
            confidence = round(float(np.max(probs)), 2)
            category = str(pred_cat)
        except Exception as e:
            print("Inference error:", e)

    urgency = 3.0
    if category == 'Medical' or any(k in text for k in ['trapped', 'dying', 'critical', 'injured']):
        urgency = 4.8
    elif category == 'Rescue & Relief' or category == 'Infrastructure Damage':
        urgency = 4.2
    elif category == 'Flood' or category == 'Fire' or category == 'Earthquake':
        urgency = 3.8

    return jsonify({
        'category': category,
        'text_severity': urgency,
        'confidence': confidence,
        'is_fake': False,
        'model_source': 'CrisisMMD v2.0 Trained Pipeline'
    })

# 2. PyTorch Computer Vision Endpoint (Authenticity & Damage Severity)
@app.route('/predict/image', methods=['POST'])
def predict_image():
    data = request.json or {}
    image_path = data.get('image_path', '')

    visual_score = 0.50
    is_authentic = True
    authenticity_reason = "Authentic disaster photo"

    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).convert('RGB')
            tensor = vision_transform(img).unsqueeze(0).to(device)

            # A. Check Authenticity (Real vs Fake/Off-Topic)
            if auth_vision_model:
                with torch.no_grad():
                    auth_logits = auth_vision_model(tensor)
                    auth_probs = torch.softmax(auth_logits, dim=1).cpu().numpy()[0]
                    is_real_prob = float(auth_probs[1]) # Class 1: Informative / Authentic
                    if is_real_prob < 0.40:
                        is_authentic = False
                        authenticity_reason = f"Image classified as off-topic or irrelevant (Authenticity Prob: {is_real_prob:.2f})"

            # B. Score Visual Damage Severity
            if dmg_vision_model and is_authentic:
                with torch.no_grad():
                    dmg_logits = dmg_vision_model(tensor)
                    dmg_probs = torch.softmax(dmg_logits, dim=1).cpu().numpy()[0]
                    # Index 0: Little/No, 1: Mild, 2: Severe
                    weighted_dmg = (dmg_probs[0] * 0.20) + (dmg_probs[1] * 0.55) + (dmg_probs[2] * 0.95)
                    visual_score = round(float(weighted_dmg), 2)
            elif not is_authentic:
                visual_score = 0.10

        except Exception as e:
            print("Vision prediction error:", e)
            visual_score = 0.60

    return jsonify({
        'visual_severity': visual_score,
        'is_authentic': is_authentic,
        'authenticity_reason': authenticity_reason,
        'model_source': 'CrisisMMD PyTorch MobileNetV3 Models'
    })

# 3. MILP Resource Dispatch Solver Endpoint
@app.route('/optimize/dispatch', methods=['POST'])
def optimize_dispatch():
    data = request.json or {}
    incidents = data.get('incidents', [])
    units = data.get('units', [])

    if not incidents or not units:
        return jsonify({'dispatch_plan': []})

    n_inc = len(incidents)
    n_units = len(units)

    cost_vector = []
    for u_idx, u in enumerate(units):
        for k_idx, k in enumerate(incidents):
            dist_km = haversine(u['latitude'], u['longitude'], k['latitude'], k['longitude'])
            travel_time_mins = (dist_km / u.get('speed_kmh', 30.0)) * 60.0
            sev = k.get('composite_severity') or k.get('severity') or 3.0
            weighted_cost = travel_time_mins / max(0.1, float(sev))
            cost_vector.append(weighted_cost)

    c = np.array(cost_vector)
    n_vars = len(c)
    integrality = np.ones(n_vars)

    A_rows = []
    b_upper = []
    b_lower = []

    for u_idx in range(n_units):
        row = np.zeros(n_vars)
        for k_idx in range(n_inc):
            row[u_idx * n_inc + k_idx] = 1.0
        A_rows.append(row)
        b_lower.append(0.0)
        b_upper.append(1.0)

    constraints = LinearConstraint(np.array(A_rows), b_lower, b_upper)
    bounds = Bounds(0, 1)

    res = milp(c=c, integrality=integrality, constraints=constraints, bounds=bounds)

    dispatch_plan = []
    if res.success:
        x_sol = res.x
        for u_idx in range(n_units):
            for k_idx in range(n_inc):
                if x_sol[u_idx * n_inc + k_idx] > 0.5:
                    u = units[u_idx]
                    k = incidents[k_idx]
                    dist_km = haversine(u['latitude'], u['longitude'], k['latitude'], k['longitude'])
                    travel_time_mins = round((dist_km / u.get('speed_kmh', 30.0)) * 60.0, 1)

                    sev = k.get('composite_severity') or k.get('severity') or 3.0
                    dispatch_plan.append({
                        'unit_code': u['unit_code'],
                        'incident_code': k['incident_code'],
                        'travel_time_minutes': travel_time_mins,
                        'xai_rationale': f"Unit {u['unit_code']} assigned: Shortest travel time of {travel_time_mins} mins to priority incident (Severity {float(sev):.1f})."
                    })

    return jsonify({'dispatch_plan': dispatch_plan})

if __name__ == '__main__':
    print("====================================================")
    print("LifeLine CrisisMMD Dual ML Microservice on http://127.0.0.1:5000")
    print("====================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)
