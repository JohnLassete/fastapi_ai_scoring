from fastapi.testclient import TestClient
from app.routes.interview import app

client = TestClient(app)

def test_interview_endpoint():
    response = client.post("/interview", json={"data": "test"})
    assert response.status_code == 200
    assert "expected_key" in response.json()  # Replace with actual expected key

def test_interview_endpoint_invalid_data():
    response = client.post("/interview", json={"data": ""})
    assert response.status_code == 400  # Replace with actual expected status code for invalid data