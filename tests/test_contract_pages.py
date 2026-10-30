from fastapi.testclient import TestClient

from app.db.session import SessionLocal, init_db
from app.main import app
from app.services.seed import run_seed


def test_spa_and_dashboard_render() -> None:
    init_db()
    with SessionLocal() as session:
        run_seed(session)
    with TestClient(app) as client:
        home = client.get("/")
        dashboard = client.get("/api/v1/dashboard")
    assert home.status_code == 200
    assert "Controle de Ciclo de Contratações" in home.text
    assert dashboard.status_code == 200
    assert dashboard.json()["total_itens"] >= 1


def test_item_creation_generates_status_history() -> None:
    init_db()
    with SessionLocal() as session:
        run_seed(session)
    with TestClient(app) as client:
        ciclo = client.get("/api/v1/ciclos").json()[0]
        software = client.get("/api/v1/softwares").json()[0]
        area = client.get("/api/v1/areas").json()[0]
        response = client.post(
            "/api/v1/itens",
            json={
                "ciclo_id": ciclo["id"],
                "software_id": software["id"],
                "tipo_movimentacao": "novo_pedido",
                "modalidade": "a_definir",
                "quantidade_solicitada": 3,
                "unidade_medida": "licenca",
                "prioridade": "media",
                "status": "cadastrado",
                "area_ids": [area["id"]],
                "processo_ids": [],
            },
        )
    assert response.status_code == 201
    assert response.json()["historico"][0]["status_novo"] == "cadastrado"
