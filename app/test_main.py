from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Application is healthy"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_error_endpoint():
    response = client.get("/error")
    assert response.status_code == 200
    assert response.json() == {"status": "Internal Server Error"}
