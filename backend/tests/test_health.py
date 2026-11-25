from fastapi.testclient import TestClient
from app.main import app
from app.schemas import LlmOut

client = TestClient(app)


def test_health_ok_and_request_id():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["ml_model"] in {"loaded", "unavailable"}
    assert "x-request-id" in res.headers


def test_llm_out_schema_is_flat():
    schema = LlmOut.model_json_schema()
    assert schema["type"] == "object"
    assert "$defs" not in schema
    assert set(schema["required"]) >= {"risk", "scam_type", "reasons", "next_steps", "confidence"}

