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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Load CrisisMMD NLP Model & Vectorizer
CRISISMMD_MODEL_PATH = os.path.join(BASE_DIR, "crisismmd_model.pkl")
CRISISMMD_VEC_PATH = os.path.join(BASE_DIR, "crisismmd_vectorizer.pkl")

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
AUTH_WEIGHTS_PATH = os.path.join(BASE_DIR, "crisismmd_vision_authenticity.pt")
DMG_WEIGHTS_PATH = os.path.join(BASE_DIR, "crisismmd_vision_damage.pt")

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

# ============================================================
# COMPREHENSIVE DISASTER LEXICON & ANTI-FAKE CLASSIFIER RULES
# ============================================================
CRISIS_DISASTER_TERMS = {
    # Floods & Heavy Water Inundation
    'flood', 'floods', 'flooding', 'flash flood', 'water level', 'drowning', 'submerged', 'river',
    'overflow', 'overflowing', 'dam', 'rain', 'heavy rain', 'deluge', 'cyclone', 'storm', 'typhoon',
    'tsunami', 'hurricane', 'monsoon', 'inundated', 'wash away', 'washed away', 'torrential',
    # Fire & High Heat Hazards
    'fire', 'flames', 'smoke', 'burning', 'blaze', 'burnt', 'cylinder', 'blast', 'explosion',
    'fire engine', 'fire brigade', 'short circuit', 'gas leak', 'toxic fumes', 'arson',
    # Earthquakes & Structural Damage
    'earthquake', 'quake', 'tremor', 'tremors', 'shaking', 'collapse', 'collapsed', 'rubble',
    'debris', 'cracks', 'caved in', 'landslide', 'mudslide', 'rockfall', 'avalanche', 'sinkhole',
    # Accidents & Collision
    'accident', 'car crash', 'bus accident', 'collision', 'overturned', 'derailed', 'pileup',
    'hit and run', 'train crash', 'bridge collapse',
    # Life Distress & Human Casualties
    'trapped', 'stuck', 'stranded', 'marooned', 'rooftop', 'screaming', 'injured', 'injuries',
    'bleeding', 'blood', 'unconscious', 'fainted', 'casualty', 'casualties', 'dead bodies',
    'dying', 'burns', 'fracture', 'broken bones', 'heart attack', 'cardiac', 'stroke',
    'chest pain', 'suffocating', 'asthma', 'breathing problem', 'pregnant', 'baby', 'infant',
    'elderly', 'patient', 'hospital', 'ambulance', 'stretcher', 'oxygen', 'first aid', 'icu',
    # Emergency Response Calls & Demands
    'help', 'help us', 'save us', 'rescue', 'sos', 'urgent', 'critical', 'emergency', 'danger',
    'life threatening', 'perished', 'missing people', 'evacuate', 'evacuation', 'relief camp',
    'boat needed', 'lifeboat', 'ropes', 'shelter needed', 'drinking water', 'food shortage',
    'electric shock', 'electrocution', 'power grid down', 'substation'
}

PRANK_HOAX_TERMS = [
    # Explicit testing & joke signals
    'test test', 'just testing', 'testing this app', 'testing the system', 'test report',
    'dummy test', 'checking if this works', 'hello world', 'sample text', 'sample report',
    'prank', 'just a prank', 'fooling', 'haha', 'hahaha', 'lol', 'lmao', 'rofl', 'lmfao',
    'just kidding', 'jk', 'fake report', 'fake emergency', 'bogus', 'hoax', 'bullshit',
    'bull shit', 'trolling', 'troll call', 'making a meme', 'for fun', 'funny emergency',
    # Absurdity & Fictional / Fantasy Entities
    'alien', 'aliens', 'ufo', 'flying saucer', 'extraterrestrial', 'zombie', 'zombies',
    'walking dead', 'vampire', 'werewolf', 'ghost in my', 'haunted house', 'monster attack',
    'godzilla', 'king kong', 'superman', 'batman', 'spiderman', 'iron man', 'avengers',
    'thanos', 'darth vader', 'illuminati', 'space invaders',
    # Lifestyle / Consumer grievances (Non-Emergency)
    'pizza', 'burger', 'zomato', 'swiggy', 'food delivery', 'dominos', 'cold food', 'late food',
    'hungry at night', 'beer', 'whiskey', 'vodka', 'party at my house', 'house party', 'clubbing',
    'pubg', 'free fire', 'fortnite', 'playstation', 'game lag', 'high ping', 'homework',
    'exam tomorrow', 'school tomorrow', 'college bunk', 'breakup', 'girlfriend broke',
    'boyfriend broke', 'crush rejected', 'wifi down', 'internet slow', 'mobile recharge',
    'talktime', 'send money', 'give me money', 'bored in my room', 'someone talk to me',
    'stole my bicycle', 'lost my pen', 'movie ticket'
]

def clean_tweet_text(text):
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'@\w+', ' ', text)
    text = re.sub(r'#([A-Z][a-z]+)', r' \1', text)
    text = re.sub(r'#(\w+)', r' \1', text)
    text = re.sub(r'&amp;', ' and ', text)
    text = re.sub(r'&lt;', ' ', text)
    text = re.sub(r'&gt;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def verify_disaster_report(text, image_path=None, category=None, needs=None):
    text_raw = str(text or '').strip()
    text_lower = text_raw.lower()

    # 1. Length & Gibberish Pre-Filter
    if len(text_raw) < 8:
        return {
            'is_fake': True,
            'authenticity_score': 0.05,
            'fake_reason': "Description is too brief (less than 8 characters) to describe a genuine disaster emergency.",
            'category': 'Unverified',
            'confidence': 0.10,
            'text_severity': 0.0,
            'visual_severity': 0.0,
            'composite_severity': 0.0,
            'warning_message': "PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. False emergency calls waste critical life-saving rescue vehicles, jeopardize real victims' lives, and are subject to legal penalties under the Disaster Management Act."
        }

    # Repeated character spam (e.g. 'aaaaaaa', 'asdasdasd')
    if len(set(text_lower)) <= 3 and len(text_lower) > 8:
        return {
            'is_fake': True,
            'authenticity_score': 0.05,
            'fake_reason': "Repeated character pattern or spam detected in distress description.",
            'category': 'Unverified',
            'confidence': 0.10,
            'text_severity': 0.0,
            'visual_severity': 0.0,
            'composite_severity': 0.0,
            'warning_message': "PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. False emergency calls waste critical life-saving rescue vehicles, jeopardize real victims' lives, and are subject to legal penalties under the Disaster Management Act."
        }

    words = re.findall(r'[a-zA-Z]+', text_lower)
    if not words:
        return {
            'is_fake': True,
            'authenticity_score': 0.05,
            'fake_reason': "No readable alphanumeric words detected in emergency description.",
            'category': 'Unverified',
            'confidence': 0.10,
            'text_severity': 0.0,
            'visual_severity': 0.0,
            'composite_severity': 0.0,
            'warning_message': "PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. False emergency calls waste critical life-saving rescue vehicles, jeopardize real victims' lives, and are subject to legal penalties under the Disaster Management Act."
        }

    avg_word_len = sum(len(w) for w in words) / max(1, len(words))
    if avg_word_len > 13 and len(words) < 4:
        return {
            'is_fake': True,
            'authenticity_score': 0.05,
            'fake_reason': "Keyboard mashing or non-dictionary gibberish detected in distress description.",
            'category': 'Unverified',
            'confidence': 0.10,
            'text_severity': 0.0,
            'visual_severity': 0.0,
            'composite_severity': 0.0,
            'warning_message': "PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. False emergency calls waste critical life-saving rescue vehicles, jeopardize real victims' lives, and are subject to legal penalties under the Disaster Management Act."
        }

    # 2. Prank, Hoax & Bullshit Term Detection
    for term in PRANK_HOAX_TERMS:
        pattern = r'\b' + re.escape(term) + r'\b'
        if re.search(pattern, text_lower):
            return {
                'is_fake': True,
                'authenticity_score': 0.08,
                'fake_reason': f"Flagged as a prank, joke, or test submission (Detected keywords: '{term}') with zero verifiable disaster indicators.",
                'category': 'Prank/Fake',
                'confidence': 0.95,
                'text_severity': 0.0,
                'visual_severity': 0.0,
                'composite_severity': 0.0,
                'warning_message': "PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. False emergency calls waste critical life-saving rescue vehicles, jeopardize real victims' lives, and are subject to legal penalties under the Disaster Management Act."
            }

    # 3. Crisis Term Density Scan
    crisis_matches = [term for term in CRISIS_DISASTER_TERMS if re.search(r'\b' + re.escape(term) + r'\b', text_lower)]
    crisis_count = len(crisis_matches)

    # 4. CrisisMMD ML Text Classification
    ml_category = "General Disaster Alert"
    ml_confidence = 0.50
    if crisismmd_model and crisismmd_vectorizer:
        try:
            clean_t = clean_tweet_text(text_raw)
            vec = crisismmd_vectorizer.transform([clean_t])
            ml_pred = crisismmd_model.predict(vec)[0]
            probs = crisismmd_model.predict_proba(vec)[0]
            ml_confidence = round(float(np.max(probs)), 2)
            ml_category = str(ml_pred)
        except Exception as e:
            print("NLP Inference error:", e)

    # If 0 disaster terms found AND text has no crisis semantics
    if crisis_count == 0:
        return {
            'is_fake': True,
            'authenticity_score': 0.18,
            'fake_reason': "No physical hazard, accident, casualty, or life-threatening distress signals detected in description.",
            'category': 'Non-Emergency',
            'confidence': 0.85,
            'text_severity': 0.0,
            'visual_severity': 0.0,
            'composite_severity': 0.0,
            'warning_message': "PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. Emergency rescue teams, boats, and ambulances are strictly prioritized for genuine life-threatening disaster events."
        }

    # 5. Computer Vision Authenticity & Damage Verification
    visual_score = 0.0
    is_image_authentic = True
    image_auth_prob = 1.0

    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path).convert('RGB')
            tensor = vision_transform(img).unsqueeze(0).to(device)

            if auth_vision_model:
                with torch.no_grad():
                    auth_logits = auth_vision_model(tensor)
                    auth_probs = torch.softmax(auth_logits, dim=1).cpu().numpy()[0]
                    image_auth_prob = float(auth_probs[1]) # Class 1: Informative / Authentic
                    if image_auth_prob < 0.35:
                        is_image_authentic = False

            if dmg_vision_model and is_image_authentic:
                with torch.no_grad():
                    dmg_logits = dmg_vision_model(tensor)
                    dmg_probs = torch.softmax(dmg_logits, dim=1).cpu().numpy()[0]
                    visual_score = round(float((dmg_probs[0] * 0.20) + (dmg_probs[1] * 0.55) + (dmg_probs[2] * 0.95)), 2)
            elif not is_image_authentic:
                visual_score = 0.10
        except Exception as e:
            print("Vision verification error:", e)

    # If photo was uploaded and detected as fake/off-topic meme with low text crisis count
    if image_path and not is_image_authentic and crisis_count < 2:
        return {
            'is_fake': True,
            'authenticity_score': 0.25,
            'fake_reason': f"Uploaded image identified as non-informative / off-topic photo (Authenticity confidence: {image_auth_prob:.2f}), combined with insufficient emergency signals in text.",
            'category': 'Unverified Media',
            'confidence': 0.80,
            'text_severity': 0.0,
            'visual_severity': 0.0,
            'composite_severity': 0.0,
            'warning_message': "PLEASE DO NOT SUBMIT FAKE DISASTER REPORTS. Uploading fake or misleading scene imagery delays genuine emergency rescue operations."
        }

    # 6. Genuine Disaster Confirmed
    authenticity_score = round(min(0.98, 0.70 + (crisis_count * 0.06)), 2)

    # Compute text severity based on urgency signals
    urgency = 3.5
    if ml_category == 'Medical' or any(k in text_lower for k in ['trapped', 'dying', 'critical', 'injured', 'bleeding', 'unconscious']):
        urgency = 4.8
    elif ml_category in ['Rescue/Affected People', 'Rescue & Relief', 'Infrastructure Damage']:
        urgency = 4.3
    elif ml_category in ['Flood', 'Fire', 'Earthquake', 'Vehicle Accidents']:
        urgency = 4.0
    elif any(k in text_lower for k in ['fire', 'flames', 'explosion', 'drowning', 'submerged']):
        urgency = 4.5

    composite_sev = round((urgency * 0.6) + (visual_score * 0.4), 1) if visual_score > 0 else urgency

    return {
        'is_fake': False,
        'authenticity_score': authenticity_score,
        'category': ml_category if ml_category != 'General Disaster Alert' else (category or 'General Disaster Alert'),
        'confidence': ml_confidence,
        'text_severity': urgency,
        'visual_severity': visual_score,
        'composite_severity': composite_sev,
        'is_authentic_image': is_image_authentic,
        'fake_reason': None,
        'matched_crisis_signals': crisis_matches[:5],
        'model_source': 'CrisisMMD Multi-Modal AI Gatekeeper'
    }

# 1. Multi-Modal Verification Gatekeeper Endpoint
@app.route('/predict/verify', methods=['POST'])
def predict_verify():
    data = request.json or {}
    text = data.get('text', '')
    image_path = data.get('image_path', None)
    category = data.get('category', None)
    needs = data.get('needs', None)

    res = verify_disaster_report(text, image_path=image_path, category=category, needs=needs)
    return jsonify(res)

# Legacy /predict/text Endpoint
@app.route('/predict/text', methods=['POST'])
def predict_text():
    data = request.json or {}
    text = data.get('text', '')
    res = verify_disaster_report(text)
    return jsonify(res)

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

def calculate_capability_match(unit_capabilities, unit_type, incident_category, incident_text, incident_demands):
    text_corpus = f"{incident_category} {incident_text} {incident_demands}".lower()
    cap_corpus = f"{unit_capabilities} {unit_type}".lower()
    
    score = 1.0
    if any(w in text_corpus for w in ['flood', 'drown', 'water', 'submerged', 'river', 'overflow', 'boat']):
        if any(w in cap_corpus for w in ['boat', 'flood', 'water', 'evacuation']):
            score += 5.0
    if any(w in text_corpus for w in ['fire', 'flame', 'smoke', 'burn', 'explosion', 'blaze']):
        if any(w in cap_corpus for w in ['fire', 'foam', 'tender', 'engine', 'extinguisher']):
            score += 5.0
    if any(w in text_corpus for w in ['medical', 'injured', 'casualty', 'bleeding', 'heart', 'oxygen', 'doctor', 'hospital', 'ambulance', 'wound', 'trauma']):
        if any(w in cap_corpus for w in ['ambulance', 'medic', 'trauma', 'als', 'oxygen', 'paramedic']):
            score += 5.0
    if any(w in text_corpus for w in ['earthquake', 'collapse', 'debris', 'rubble', 'trapped', 'building', 'structure']):
        if any(w in cap_corpus for w in ['ndrf', 'search', 'extrication', 'cutter', 'radar', 'structural']):
            score += 5.0
    if any(w in text_corpus for w in ['food', 'water', 'ration', 'starv', 'hunger', 'blanket', 'clothes', 'supplies']):
        if any(w in cap_corpus for w in ['relief', 'truck', 'supplies', 'food', 'logistics', 'purification']):
            score += 5.0

    return score

# 3. SciPy MILP & Nearest-Station Resource Allocation Solver
@app.route('/optimize/dispatch', methods=['POST'])
def optimize_dispatch():
    data = request.json or {}
    incidents = data.get('incidents', [])
    units = data.get('units') or data.get('vehicles') or []

    if not incidents or not units:
        return jsonify({'dispatch_plan': []})

    n_inc = len(incidents)
    n_units = len(units)

    c = []
    # Cost minimizes travel time from closest station with capability match
    for u_idx, u in enumerate(units):
        for k_idx, k in enumerate(incidents):
            dist_km = haversine(u['latitude'], u['longitude'], k['latitude'], k['longitude'])
            speed = float(u.get('speed_kmh') or 35.0)
            cat = str(k.get('category') or '').lower()
            if any(hazard in cat for hazard in ['flood', 'fire', 'earthquake']):
                speed = max(12.0, speed * 0.85)
            travel_time_mins = (dist_km / speed) * 60.0
            sev = float(k.get('composite_severity') or k.get('severity') or 3.0)

            cap_score = calculate_capability_match(
                u.get('capabilities', ''),
                u.get('type', ''),
                k.get('category', ''),
                k.get('description', ''),
                k.get('demands', '')
            )
            
            cost = (travel_time_mins * 2.0 / (cap_score * max(0.5, sev))) - (1500.0 * sev * cap_score)
            c.append(cost)

    c = np.array(c)
    n_vars = len(c)
    integrality = np.ones(n_vars)

    A_rows = []
    b_upper = []
    b_lower = []

    # Constraint 1: Each response unit assigned at most once
    for u_idx in range(n_units):
        row = np.zeros(n_vars)
        for k_idx in range(n_inc):
            row[u_idx * n_inc + k_idx] = 1.0
        A_rows.append(row)
        b_lower.append(0.0)
        b_upper.append(1.0)

    # Constraint 2: Each incident receives at most 1 unit
    for k_idx in range(n_inc):
        row = np.zeros(n_vars)
        for u_idx in range(n_units):
            row[u_idx * n_inc + k_idx] = 1.0
        A_rows.append(row)
        b_lower.append(0.0)
        b_upper.append(1.0)

    constraints = LinearConstraint(np.array(A_rows), b_lower, b_upper)
    bounds = Bounds(0, 1)

    res = milp(c=c, integrality=integrality, constraints=constraints, bounds=bounds)

    dispatch_plan = []
    assigned_units = set()
    assigned_incidents = set()

    if res.success:
        x_sol = res.x
        for u_idx in range(n_units):
            for k_idx in range(n_inc):
                if x_sol[u_idx * n_inc + k_idx] > 0.5:
                    u = units[u_idx]
                    k = incidents[k_idx]
                    dist_km = haversine(u['latitude'], u['longitude'], k['latitude'], k['longitude'])
                    speed = float(u.get('speed_kmh') or 35.0)
                    cat = str(k.get('category') or '').lower()
                    if any(hazard in cat for hazard in ['flood', 'fire', 'earthquake']):
                        speed = max(12.0, speed * 0.85)
                    travel_time_mins = round((dist_km / speed) * 60.0, 1)

                    u_code = u.get('unit_code') or u.get('id') or f"Unit-{u_idx+1}"
                    k_code = k.get('incident_code') or k.get('id') or f"Inc-{k_idx+1}"
                    st_name = u.get('station_name') or 'Nearest Emergency Response Station'
                    st_code = u.get('station_code') or 'STATION-01'
                    u_type = u.get('type') or 'Emergency Rescue Vehicle'
                    supplies = u.get('supplies_payload') or 'Standard Emergency Rescue Supplies'

                    dispatch_plan.append({
                        'unit_code': u_code,
                        'incident_code': k_code,
                        'station_code': st_code,
                        'station_name': st_name,
                        'unit_type': u_type,
                        'travel_time_minutes': travel_time_mins,
                        'distance_km': round(dist_km, 2),
                        'supplies_payload': supplies,
                        'xai_rationale': f"Dispatched from nearest station '{st_name}' ({round(dist_km, 1)} km away). Fastest transit arrival: {travel_time_mins} mins with specialized {u_type} carrying life-saving supplies: {supplies}."
                    })
                    assigned_units.add(u_code)
                    assigned_incidents.add(k_code)

    # Deterministic nearest-station greedy fallback for any unassigned incidents
    for k in incidents:
        k_code = k.get('incident_code') or k.get('id')
        if k_code in assigned_incidents:
            continue
        best_u = None
        min_eff_time = float('inf')
        best_dist = 0
        best_time = 0

        for u in units:
            u_code = u.get('unit_code') or u.get('id')
            if u_code in assigned_units:
                continue
            dist_km = haversine(u['latitude'], u['longitude'], k['latitude'], k['longitude'])
            speed = float(u.get('speed_kmh') or 35.0)
            time_mins = (dist_km / speed) * 60.0
            cap_score = calculate_capability_match(
                u.get('capabilities', ''),
                u.get('type', ''),
                k.get('category', ''),
                k.get('description', ''),
                k.get('demands', '')
            )
            eff_time = time_mins / cap_score
            if eff_time < min_eff_time:
                min_eff_time = eff_time
                best_u = u
                best_dist = dist_km
                best_time = time_mins

        if best_u:
            u_code = best_u.get('unit_code') or best_u.get('id')
            assigned_units.add(u_code)
            assigned_incidents.add(k_code)
            st_name = best_u.get('station_name') or 'Nearest Emergency Response Station'
            st_code = best_u.get('station_code') or 'STATION-01'
            u_type = best_u.get('type') or 'Emergency Rescue Vehicle'
            supplies = best_u.get('supplies_payload') or 'Standard Emergency Rescue Supplies'

            dispatch_plan.append({
                'unit_code': u_code,
                'incident_code': k_code,
                'station_code': st_code,
                'station_name': st_name,
                'unit_type': u_type,
                'travel_time_minutes': round(best_time, 1),
                'distance_km': round(best_dist, 2),
                'supplies_payload': supplies,
                'xai_rationale': f"Dispatched from nearest station '{st_name}' ({round(best_dist, 1)} km away). Fastest transit arrival: {round(best_time, 1)} mins with specialized {u_type} carrying life-saving supplies: {supplies}."
            })

    return jsonify({'dispatch_plan': dispatch_plan})

if __name__ == '__main__':
    print("====================================================")
    print("LifeLine CrisisMMD Dual ML Microservice on http://127.0.0.1:5000")
    print("====================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)
