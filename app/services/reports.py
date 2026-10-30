import csv
from datetime import date, timedelta
from io import BytesIO, StringIO
from typing import Any

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models.domain import Area, Contrato, ItemCiclo


def item_rows(items: list[ItemCiclo]) -> list[dict[str, Any]]:
    rows = []
    for item in items:
        rows.append(
            {
                "ciclo": item.ciclo.nome if item.ciclo else "",
                "software": item.software.nome if item.software else "",
                "tipo_movimentacao": item.tipo_movimentacao,
                "modalidade": item.modalidade,
                "status": item.status,
                "prioridade": item.prioridade,
                "quantidade_solicitada": item.quantidade_solicitada,
                "quantidade_adicional": item.quantidade_adicional,
                "areas": "; ".join(area.sigla for area in item.areas),
                "processos": "; ".join(processo.numero for processo in item.processos),
                "contrato": item.contrato.numero if item.contrato else "",
                "vencimento_subscricao": item.vencimento_subscricao.isoformat() if item.vencimento_subscricao else "",
                "lote": item.lote or "",
                "observacoes": item.observacoes or "",
            }
        )
    return rows


def rows_to_csv(rows: list[dict[str, Any]]) -> str:
    buffer = StringIO()
    fieldnames = list(rows[0].keys()) if rows else ["sem_dados"]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def rows_to_xlsx(rows: list[dict[str, Any]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "relatorio"
    headers = list(rows[0].keys()) if rows else ["sem_dados"]
    sheet.append(headers)
    for row in rows:
        sheet.append([row.get(header) for header in headers])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def dashboard(db: Session, ciclo_id: int | None = None) -> dict[str, Any]:
    query = db.query(ItemCiclo)
    if ciclo_id:
        query = query.filter(ItemCiclo.ciclo_id == ciclo_id)
    items = query.all()
    today = date.today()
    software_ids = {item.software_id for item in items}
    vencimentos = {}
    for days in [180, 120, 90, 60, 30]:
        limit = today + timedelta(days=days)
        vencimentos[f"ate_{days}_dias"] = sum(
            1 for item in items if item.vencimento_subscricao and today <= item.vencimento_subscricao <= limit
        )
    return {
        "total_itens": len(items),
        "total_softwares_distintos": len(software_ids),
        "por_status": count_by(items, "status"),
        "por_modalidade": count_by(items, "modalidade"),
        "por_prioridade": count_by(items, "prioridade"),
        "vencimentos": vencimentos,
        "vencidos": sum(1 for item in items if item.vencimento_subscricao and item.vencimento_subscricao < today),
        "itens_sem_processo_sei": sum(1 for item in items if not item.processos),
        "itens_sem_quantidade_definida": sum(1 for item in items if item.quantidade_solicitada is None),
    }


def count_by(items: list[ItemCiclo], attr: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        key = str(getattr(item, attr))
        result[key] = result.get(key, 0) + 1
    return result


def consolidated_by_software(db: Session, ciclo_id: int | None = None) -> list[dict[str, Any]]:
    query = db.query(ItemCiclo)
    if ciclo_id:
        query = query.filter(ItemCiclo.ciclo_id == ciclo_id)
    grouped: dict[int, dict[str, Any]] = {}
    for item in query.all():
        software = item.software
        if not software:
            continue
        entry = grouped.setdefault(
            software.id,
            {
                "software_id": software.id,
                "software": software.nome,
                "quantidade_solicitada": 0.0,
                "quantidade_adicional": 0.0,
                "areas": set(),
                "processos": set(),
                "contratos": set(),
                "vencimentos": set(),
            },
        )
        entry["quantidade_solicitada"] += item.quantidade_solicitada or 0
        entry["quantidade_adicional"] += item.quantidade_adicional or 0
        entry["areas"].update(area.sigla for area in item.areas)
        entry["processos"].update(processo.numero for processo in item.processos)
        if item.contrato:
            entry["contratos"].add(item.contrato.numero)
        if item.vencimento_subscricao:
            entry["vencimentos"].add(item.vencimento_subscricao)
    return [
        {
            **entry,
            "areas": sorted(entry["areas"]),
            "processos": sorted(entry["processos"]),
            "contratos": sorted(entry["contratos"]),
            "vencimentos": sorted(entry["vencimentos"]),
        }
        for entry in grouped.values()
    ]


def by_area(db: Session, area_id: int | None = None) -> list[dict[str, Any]]:
    areas = db.query(Area).filter(Area.id == area_id).all() if area_id else db.query(Area).all()
    rows = []
    for area in areas:
        for item in area.itens:
            rows.append(
                {
                    "area_id": area.id,
                    "sigla": area.sigla,
                    "area": area.nome,
                    "software": item.software.nome if item.software else "",
                    "quantidade_solicitada": item.quantidade_solicitada,
                    "processo": "; ".join(processo.numero for processo in item.processos) or None,
                    "status": item.status,
                    "modalidade": item.modalidade,
                }
            )
    return rows


def expirations(db: Session, days: int | None = None) -> list[dict[str, Any]]:
    today = date.today()
    limit = today + timedelta(days=days or 3650)
    contracts = (
        db.query(Contrato)
        .filter(Contrato.vencimento_subscricao.is_not(None))
        .filter(Contrato.vencimento_subscricao <= limit)
        .order_by(Contrato.vencimento_subscricao)
        .all()
    )
    return [
        {
            "contrato": contract.numero,
            "software": contract.software.nome if contract.software else "",
            "fornecedor": contract.fornecedor,
            "vencimento_subscricao": contract.vencimento_subscricao,
            "data_fim": contract.data_fim,
            "status": contract.status,
            "dias_para_vencer": (contract.vencimento_subscricao - today).days if contract.vencimento_subscricao else None,
        }
        for contract in contracts
    ]
