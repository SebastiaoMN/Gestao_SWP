from pathlib import Path

REQUIRED_ENTITIES = [
    "class Ciclo",
    "class Software",
    "class Area",
    "class Processo",
    "class Contrato",
    "class ItemCiclo",
    "class ItemHistorico",
]
REQUIRED_ITEM_FIELDS = [
    "tipo_movimentacao",
    "modalidade",
    "quantidade_solicitada",
    "prioridade",
    "status",
    "justificativa",
    "risco",
]


def test_domain_model_declares_mvp_entities_and_item_fields() -> None:
    source = Path("app/models/domain.py").read_text(encoding="utf-8")
    for entity in REQUIRED_ENTITIES:
        assert entity in source
    for field in REQUIRED_ITEM_FIELDS:
        assert field in source
