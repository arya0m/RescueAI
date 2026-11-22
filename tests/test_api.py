"""
RescueAI Operations API Automated Pytest Suite
Validates all endpoints, startup caching, data integrity, and ML inference.
"""

import io
import pytest
from fastapi.testclient import TestClient
from rescueai.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_meta_endpoint(client):
    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "Logistic Regression (Balanced)"
    assert data["test_macro_f1"] == pytest.approx(0.4746, abs=1e-4)
    assert data["test_accuracy"] == pytest.approx(0.5060, abs=1e-4)
    assert data["dataset_name"] == "CrisisMMD v2.0"
    assert data["disaster_events_count"] == 7
    assert len(data["categories"]) == 5
    assert data["categories"][0]["name"] == "Affected People & Medical Emergencies"
    assert data["categories"][0]["urgency"] == "High"


def test_events_endpoint(client):
    response = client.get("/api/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 7
    
    event_ids = [e["event_id"] for e in events]
    assert "hurricane_harvey" in event_ids
    assert "mexico_earthquake" in event_ids
    assert "california_wildfires" in event_ids
    
    # Verify coordinates and counts
    for ev in events:
        assert isinstance(ev["lat"], float)
        assert isinstance(ev["lon"], float)
        assert ev["total_messages"] > 0
        assert "counts_by_class" in ev
        assert "high_urgency_percent" in ev


def test_messages_endpoint(client):
    response = client.get("/api/messages?split=test&page=1&size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2237  # Real test set count
    assert data["page"] == 1
    assert data["size"] == 10
    assert len(data["items"]) == 10
    
    msg = data["items"][0]
    assert "tweet_id" in msg
    assert "tweet_text" in msg
    assert "timestamp" in msg
    assert "2017-" in msg["timestamp"]  # Real 2017 snowflake date
    assert "probabilities" in msg


def test_messages_filtering(client):
    # Filter by event
    response = client.get("/api/messages?split=test&event=hurricane_harvey&page=1&size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 572  # Known Harvey count in test set
    for item in data["items"]:
        assert item["event_name"] == "hurricane_harvey"

    # Filter by true class
    response_cls = client.get("/api/messages?split=test&true_cls=0&page=1&size=5")
    assert response_cls.status_code == 200
    for item in response_cls.json()["items"]:
        assert item["true_label"] == 0


def test_message_detail(client):
    # Get a real tweet ID from test set
    list_res = client.get("/api/messages?split=test&page=1&size=1")
    tweet_id = list_res.json()["items"][0]["tweet_id"]
    
    response = client.get(f"/api/messages/{tweet_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["tweet_id"] == tweet_id
    assert "terms" in detail
    assert "status" in detail


def test_timeline_endpoint(client):
    response = client.get("/api/timeline?bucket=day")
    assert response.status_code == 200
    buckets = response.json()
    assert len(buckets) > 0
    first = buckets[0]
    assert "time" in first
    assert "total" in first
    assert "counts" in first


def test_replay_endpoint(client):
    response = client.get("/api/replay?event=california_wildfires")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 216  # California wildfires in test set
    
    # Confirm strictly chronological ordering
    timestamps = [m["timestamp"] for m in messages]
    assert timestamps == sorted(timestamps)


def test_predict_endpoint(client):
    payload = {"text": "URGENT: Family trapped in flooded house, medical supplies needed!"}
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["predicted_label"] in range(5)
    assert "predicted_category" in data
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0
    assert "terms" in data
    assert len(data["terms"]) > 0
    assert "is_low_confidence" in data


def test_predict_ablation(client):
    payload = {
        "text": "Medical supplies urgently needed for injured victims in shelter",
        "remove": ["medical", "injured"]
    }
    response = client.post("/api/predict/ablate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "original" in data
    assert "ablated" in data
    assert "confidence_delta" in data
    assert data["removed_tokens"] == ["medical", "injured"]


def test_predict_batch_csv(client):
    csv_content = "text\nFlooded streets in downtown\nEarthquake tremors felt strongly\nJust chilling watching tv\n"
    files = {"file": ("test_batch.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    
    response = client.post("/api/predict/batch", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["total_rows"] == 3
    assert len(data["predictions"]) == 3
    assert "category_summary" in data


def test_models_benchmark_endpoint(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    models_list = response.json()
    assert len(models_list) == 4
    
    champion = next(m for m in models_list if m["is_selected"])
    assert "Logistic Regression" in champion["model"]
    assert champion["macro_f1"] == pytest.approx(0.4746, abs=1e-4)


def test_confusion_matrix_endpoint(client):
    response = client.get("/api/models/logistic_regression/confusion?normalize=false")
    assert response.status_code == 200
    data = response.json()
    matrix = data["matrix"]
    assert len(matrix) == 5
    assert len(matrix[0]) == 5
    assert sum(sum(row) for row in matrix) == 2237  # Total test samples


def test_confusion_cell_endpoint(client):
    response = client.get("/api/models/logistic_regression/confusion/cell?true=0&pred=0&page=1&size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["true_label"] == 0
    assert data["predicted_label"] == 0
    assert data["total_count"] > 0
    assert len(data["items"]) <= 5


def test_threshold_analysis_endpoint(client):
    response = client.get("/api/models/logistic_regression/threshold?t=0.6")
    assert response.status_code == 200
    data = response.json()
    assert data["threshold"] == 0.6
    assert data["total_messages"] == 2237
    assert data["flagged_count"] + data["retained_count"] == 2237
    assert "retained_macro_f1" in data


def test_terms_endpoint(client):
    response = client.get("/api/terms")
    assert response.status_code == 200
    terms_data = response.json()
    assert len(terms_data) == 5
    for cat in terms_data:
        assert len(cat["terms"]) > 0
        assert "weight" in cat["terms"][0]


def test_wordcloud_endpoint(client):
    response = client.get("/api/wordcloud/0.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 1000


def test_triage_status_flow(client):
    # Pick a tweet
    list_res = client.get("/api/messages?split=test&page=1&size=1")
    tweet_id = list_res.json()["items"][0]["tweet_id"]
    
    # Update status to flagged
    put_res = client.put(f"/api/status/{tweet_id}", json={"status": "flagged"})
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "flagged"
    
    # Check that message now has status 'flagged'
    get_res = client.get(f"/api/messages/{tweet_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "flagged"


def test_feedback_and_history(client):
    # Submit feedback
    fb_payload = {
        "raw_text": "Sample test emergency message for audit verification",
        "predicted_label": 0,
        "is_correct": True
    }
    fb_res = client.post("/api/feedback", json=fb_payload)
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "saved"
    
    # Check history
    hist_res = client.get("/api/history?page=1&size=10")
    assert hist_res.status_code == 200
    assert hist_res.json()["total"] > 0
