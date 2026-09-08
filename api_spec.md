# LifeLine System API Specifications & Data Schema Contract

This document defines the exact REST API endpoints, JSON request/response payloads, and WebSocket events connecting the **Full-Stack Developer Interface**, **ML Engineer 1 (NLP/Deduplication)**, and **ML Engineer 2 (CV/Optimization)**.

---

## 1. Citizen Incident Submission Endpoint

* **Endpoint**: `POST /api/incidents/report`
* **Content-Type**: `multipart/form-data` or `application/json`

### Request Payload (JSON):
```json
{
  "reporter_name": "Vijay Katiyar",
  "reporter_phone": "+91 9876543210",
  "description": "Severe flooding on main street, 2nd floor submerged, 3 elderly people trapped needing evacuation",
  "latitude": 28.6752,
  "longitude": 77.5020,
  "timestamp": "2026-08-14T19:00:00Z",
  "image_url": "https://lifeline-bucket.s3.amazonaws.com/uploads/flood_image_01.jpg"
}
```

### Response Payload:
```json
{
  "status": "success",
  "incident_id": "INC-20260814-001",
  "is_duplicate": false,
  "incident_category": "Flood",
  "severity_level": 4,
  "composite_score": 4.25,
  "assigned_status": "QUEUED_FOR_DISPATCH",
  "message": "Incident report logged and categorized successfully."
}
```

---

## 2. ML Engineer 1 Endpoints (NLP & Deduplication)

### A. Text Category & Urgency Classification
* **Endpoint**: `POST /api/ml/classify-text`
* **Content-Type**: `application/json`

#### Request Payload:
```json
{
  "text": "Severe flooding on main street, 2nd floor submerged, 3 elderly people trapped needing evacuation"
}
```

#### Response Payload:
```json
{
  "category": "Flood",
  "category_probabilities": {
    "Flood": 0.94,
    "Fire": 0.02,
    "Earthquake": 0.01,
    "Landslide": 0.01,
    "Medical": 0.02
  },
  "text_urgency_score": 4,
  "extracted_entities": {
    "trapped_count": 3,
    "urgency_keywords": ["flooding", "submerged", "trapped", "evacuation"]
  }
}
```

### B. Spatial-Temporal Deduplication Check
* **Endpoint**: `POST /api/ml/deduplicate`
* **Content-Type**: `application/json`

#### Request Payload:
```json
{
  "new_text": "Water levels reaching 2nd floor near main market road, family trapped",
  "latitude": 28.6755,
  "longitude": 77.5022,
  "active_incidents": [
    {
      "incident_id": "INC-20260814-001",
      "text": "Severe flooding on main street, 2nd floor submerged, 3 elderly people trapped needing evacuation",
      "latitude": 28.6752,
      "longitude": 77.5020,
      "timestamp": "2026-08-14T19:00:00Z"
    }
  ]
}
```

#### Response Payload:
```json
{
  "is_duplicate": true,
  "matched_incident_id": "INC-20260814-001",
  "similarity_score": 0.86,
  "action": "INCREMENT_CONFIRMATION_COUNT"
}
```

---

## 3. ML Engineer 2 Endpoints (CV & Optimization)

### A. Computer Vision Damage Verification
* **Endpoint**: `POST /api/ml/verify-image`
* **Content-Type**: `application/json`

#### Request Payload:
```json
{
  "image_url": "https://lifeline-bucket.s3.amazonaws.com/uploads/flood_image_01.jpg"
}
```

#### Response Payload:
```json
{
  "visual_damage_score": 0.85,
  "detected_hazards": ["deep_water", "submerged_structure"],
  "is_authentic": true
}
```

### B. Resource Optimization Dispatch Solver
* **Endpoint**: `POST /api/ml/optimize-dispatch`
* **Content-Type**: `application/json`

#### Request Payload:
```json
{
  "unassigned_incidents": [
    {
      "incident_id": "INC-20260814-001",
      "latitude": 28.6752,
      "longitude": 77.5020,
      "composite_severity": 4.5,
      "required_capacity": 3
    }
  ],
  "available_units": [
    {
      "unit_id": "RESCUE-BOAT-01",
      "type": "Rescue Boat",
      "latitude": 28.6800,
      "longitude": 77.4950,
      "capacity": 4,
      "avg_speed_kmh": 20
    }
  ]
}
```

#### Response Payload:
```json
{
  "dispatch_plan": [
    {
      "unit_id": "RESCUE-BOAT-01",
      "incident_id": "INC-20260814-001",
      "estimated_travel_time_minutes": 12.4,
      "xai_explanation": "RESCUE-BOAT-01 assigned: Nearest available unit (12.4 mins travel time), capacity matches 3 victims, severity rating 4.5 prioritized."
    }
  ],
  "unserved_incidents": []
}
```

---

## 4. WebSocket Live Dashboard Feed

* **Endpoint**: `ws://server/ws/incidents`
* **Event**: `INCIDENT_UPDATE`

```json
{
  "event_type": "INCIDENT_ADDED",
  "data": {
    "incident_id": "INC-20260814-001",
    "category": "Flood",
    "severity": 4.5,
    "latitude": 28.6752,
    "longitude": 77.5020,
    "status": "DISPATCHED",
    "assigned_unit": "RESCUE-BOAT-01"
  }
}
```
