from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.domain import (
    Area,
    Contrato,
    ItemCiclo,
    ItemStatus,
    Modalidade,
    Processo,
    Software,
    TipoMovimentacao,
)
from app.schemas.domain import ItemCicloCreate, ItemCicloUpdate

PROCESSO_REQUIRED_STATUSES = {
    ItemStatus.EM_INSTRUCAO_PROCESSUAL,
    ItemStatus.ENCAMINHADO_LICITACAO,
    ItemStatus.ENCAMINHADO_RENOVACAO,
    ItemStatus.ENCAMINHADO_ADITIVO,
    ItemStatus.ENCAMINHADO_CONTRATACAO_DIRETA,
}


def enum_value(value: object) -> object:
    return getattr(value, "value", value)


def validate_item_rules(
    db: Session,
    payload: ItemCicloCreate | ItemCicloUpdate,
    current: ItemCiclo | None = None,
) -> None:
    data = payload.model_dump(exclude_unset=True)
    merged = {}
    if current is not None:
        for key in [
            "ciclo_id",
            "software_id",
            "tipo_movimentacao",
            "modalidade",
            "contrato_id",
            "vencimento_subscricao",
            "quantidade_solicitada",
            "justificativa",
            "status",
            "motivo_nao_renovacao",
            "software_substituto_id",
        ]:
            merged[key] = getattr(current, key)
        merged["area_ids"] = [area.id for area in current.areas]
        merged["processo_ids"] = [processo.id for processo in current.processos]
    merged.update(data)

    area_ids = merged.get("area_ids") or []
    processo_ids = merged.get("processo_ids") or []
    quantidade_solicitada = merged.get("quantidade_solicitada")
    justificativa = merged.get("justificativa")
    contrato_id = merged.get("contrato_id")
    vencimento = merged.get("vencimento_subscricao")
    status = ItemStatus(enum_value(merged.get("status")))
    modalidade = Modalidade(enum_value(merged.get("modalidade")))
    tipo_movimentacao = TipoMovimentacao(enum_value(merged.get("tipo_movimentacao")))

    if not merged.get("ciclo_id"):
        raise HTTPException(status_code=422, detail="Todo item deve pertencer a um ciclo.")
    if not merged.get("software_id"):
        raise HTTPException(status_code=422, detail="Todo item deve possuir software.")
    if not area_ids:
        raise HTTPException(status_code=422, detail="Todo item deve possuir ao menos uma area.")
    if quantidade_solicitada is None and not justificativa:
        raise HTTPException(
            status_code=422,
            detail="Informe quantidade solicitada ou justificativa para quantidade indefinida.",
        )
    if status in PROCESSO_REQUIRED_STATUSES and not processo_ids and not justificativa:
        raise HTTPException(
            status_code=422,
            detail="Este status exige processo SEI/DOD vinculado ou justificativa.",
        )
    if contrato_id and not vencimento:
        contrato = db.get(Contrato, contrato_id)
        if not contrato or not contrato.vencimento_subscricao:
            raise HTTPException(
                status_code=422,
                detail="Contrato/subscricao vigente exige vencimento informado.",
            )
    software = db.get(Software, merged.get("software_id"))
    if (
        software
        and software.software_livre
        and modalidade != Modalidade.HOMOLOGACAO_SOFTWARE_LIVRE
        and tipo_movimentacao != TipoMovimentacao.HOMOLOGACAO
    ):
        raise HTTPException(
            status_code=422,
            detail="Software livre deve usar fluxo de homologacao.",
        )
    if status == ItemStatus.NAO_RENOVADO and not merged.get("motivo_nao_renovacao"):
        raise HTTPException(status_code=422, detail="Informe o motivo da nao renovacao.")


def apply_item_relationships(
    db: Session,
    item: ItemCiclo,
    area_ids: list[int] | None,
    processo_ids: list[int] | None,
) -> None:
    if area_ids is not None:
        item.areas = db.query(Area).filter(Area.id.in_(area_ids)).all()
    if processo_ids is not None:
        item.processos = db.query(Processo).filter(Processo.id.in_(processo_ids)).all()


def normalize_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])
