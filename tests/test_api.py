from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_options_expose_business_lists() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/options")
    assert response.status_code == 200
    data = response.json()
    assert "renovacao" in data["tipos_movimentacao"]
    assert "homologacao_software_livre" in data["modalidades"]
    assert "critica" in data["prioridades"]
