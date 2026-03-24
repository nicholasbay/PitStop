from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app

client = TestClient(app)
settings = Settings()

def test_health_check():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {"message": f"{settings.APP_TITLE} is running"}
