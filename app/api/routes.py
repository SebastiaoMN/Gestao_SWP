from collections.abc import Iterable
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_session
from app.models.domain import (
    Area,
    Ciclo,
    CicloStatus,
    Contrato,
    ContratoStatus,
    ItemCiclo,
    ItemHistorico,
    ItemStatus,
    Modalidade,
    Prioridade,
    Processo,
    ProcessoStatus,
    ProcessoTipo,
    Semestre,
    Software,
    TipoMovimentacao,
)
from app.schemas.domain import (
    AreaCreate,
    AreaRead,
    AreaUpdate,
    CicloCreate,
    CicloRead,
    CicloUpdate,
    ConsolidadoSoftwareRead,
    ContratoCreate,
    ContratoRead,
    ContratoUpdate,
    DashboardRead,
    ImportResult,
    ItemCicloCreate,
    ItemCicloRead,
    ItemCicloUpdate,
    ProcessoCreate,
    ProcessoRead,
    ProcessoUpdate,
    SoftwareCreate,
    SoftwareRead,
    SoftwareUpdate,
    VisaoAreaRead,
)
from app.services.business import apply_item_relationships, validate_item_rules
from app.services.reports import (
    by_area,
    consolidated_by_software,
    dashboard,
    expirations,
    item_rows,
    rows_to_csv,
    rows_to_xlsx,
)

router = APIRouter(prefix="/api/v1")
SessionDep = Depends(get_session)

ITEM_LOADS = (
    selectinload(ItemCiclo.ciclo),
    selectinload(ItemCiclo.software),
    selectinload(ItemCiclo.contrato).selectinload(Contrato.software),
    selectinload(ItemCiclo.areas),
    selectinload(ItemCiclo.processos),
    selectinload(ItemCiclo.historico),
)


def current_user(request: Request) -> str:
    return request.headers.get("X-User-Profile", "administrador")


def commit_or_409(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Registro duplicado ou relacionamento invalido.") from exc


def get_or_404(db: Session, model: type, item_id: int):
    obj = db.get(model, item_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    return obj


def update_model(obj: object, payload: Any, exclude: set[str] | None = None) -> None:
    for key, value in payload.model_dump(exclude_unset=True).items():
        if exclude and key in exclude:
            continue
        setattr(obj, key, getattr(value, "value", value))


def enum_values(enum_cls: type) -> list[str]:
    return [item.value for item in enum_cls]


@router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/auth/me", tags=["auth"])
def me(user: str = Depends(current_user)) -> dict[str, str]:
    return {"profile": user}


@router.get("/options", tags=["options"])
def options() -> dict[str, list[str]]:
    return {
        "semestres": enum_values(Semestre),
        "ciclo_status": enum_values(CicloStatus),
        "tipos_movimentacao": enum_values(TipoMovimentacao),
        "modalidades": enum_values(Modalidade),
        "status": enum_values(ItemStatus),
        "prioridades": enum_values(Prioridade),
        "processo_tipos": enum_values(ProcessoTipo),
        "processo_status": enum_values(ProcessoStatus),
        "contrato_status": enum_values(ContratoStatus),
    }


@router.post("/ciclos", response_model=CicloRead, status_code=201, tags=["ciclos"])
def create_ciclo(payload: CicloCreate, db: Session = SessionDep):
    obj = Ciclo(**{k: getattr(v, "value", v) for k, v in payload.model_dump().items()})
    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.get("/ciclos", response_model=list[CicloRead], tags=["ciclos"])
def list_ciclos(ano: int | None = None, semestre: Semestre | None = None, db: Session = SessionDep):
    query = db.query(Ciclo)
    if ano:
        query = query.filter(Ciclo.ano == ano)
    if semestre:
        query = query.filter(Ciclo.semestre == semestre.value)
    return query.order_by(Ciclo.ano.desc(), Ciclo.semestre).all()


@router.get("/ciclos/{item_id}", response_model=CicloRead, tags=["ciclos"])
def get_ciclo(item_id: int, db: Session = SessionDep):
    return get_or_404(db, Ciclo, item_id)


@router.put("/ciclos/{item_id}", response_model=CicloRead, tags=["ciclos"])
def update_ciclo(item_id: int, payload: CicloUpdate, db: Session = SessionDep):
    obj = get_or_404(db, Ciclo, item_id)
    update_model(obj, payload)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.delete("/ciclos/{item_id}", status_code=204, tags=["ciclos"])
def delete_ciclo(item_id: int, db: Session = SessionDep):
    db.delete(get_or_404(db, Ciclo, item_id))
    commit_or_409(db)


@router.post("/softwares", response_model=SoftwareRead, status_code=201, tags=["softwares"])
def create_software(payload: SoftwareCreate, db: Session = SessionDep):
    obj = Software(**payload.model_dump())
    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.get("/softwares", response_model=list[SoftwareRead], tags=["softwares"])
def list_softwares(search: str | None = None, ativo: bool | None = None, db: Session = SessionDep):
    query = db.query(Software)
    if search:
        query = query.filter(Software.nome.ilike(f"%{search}%"))
    if ativo is not None:
        query = query.filter(Software.ativo == ativo)
    return query.order_by(Software.nome).all()


@router.get("/softwares/{item_id}", response_model=SoftwareRead, tags=["softwares"])
def get_software(item_id: int, db: Session = SessionDep):
    return get_or_404(db, Software, item_id)


@router.put("/softwares/{item_id}", response_model=SoftwareRead, tags=["softwares"])
def update_software(item_id: int, payload: SoftwareUpdate, db: Session = SessionDep):
    obj = get_or_404(db, Software, item_id)
    update_model(obj, payload)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.delete("/softwares/{item_id}", status_code=204, tags=["softwares"])
def delete_software(item_id: int, db: Session = SessionDep):
    db.delete(get_or_404(db, Software, item_id))
    commit_or_409(db)


@router.post("/areas", response_model=AreaRead, status_code=201, tags=["areas"])
def create_area(payload: AreaCreate, db: Session = SessionDep):
    obj = Area(**payload.model_dump())
    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.get("/areas", response_model=list[AreaRead], tags=["areas"])
def list_areas(search: str | None = None, ativo: bool | None = None, db: Session = SessionDep):
    query = db.query(Area)
    if search:
        query = query.filter((Area.nome.ilike(f"%{search}%")) | (Area.sigla.ilike(f"%{search}%")))
    if ativo is not None:
        query = query.filter(Area.ativo == ativo)
    return query.order_by(Area.sigla).all()


@router.get("/areas/{item_id}", response_model=AreaRead, tags=["areas"])
def get_area(item_id: int, db: Session = SessionDep):
    return get_or_404(db, Area, item_id)


@router.put("/areas/{item_id}", response_model=AreaRead, tags=["areas"])
def update_area(item_id: int, payload: AreaUpdate, db: Session = SessionDep):
    obj = get_or_404(db, Area, item_id)
    update_model(obj, payload)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.delete("/areas/{item_id}", status_code=204, tags=["areas"])
def delete_area(item_id: int, db: Session = SessionDep):
    db.delete(get_or_404(db, Area, item_id))
    commit_or_409(db)


@router.post("/processos", response_model=ProcessoRead, status_code=201, tags=["processos"])
def create_processo(payload: ProcessoCreate, db: Session = SessionDep):
    obj = Processo(**{k: getattr(v, "value", v) for k, v in payload.model_dump().items()})
    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.get("/processos", response_model=list[ProcessoRead], tags=["processos"])
def list_processos(search: str | None = None, db: Session = SessionDep):
    query = db.query(Processo)
    if search:
        query = query.filter(Processo.numero.ilike(f"%{search}%"))
    return query.order_by(Processo.numero).all()


@router.get("/processos/{item_id}", response_model=ProcessoRead, tags=["processos"])
def get_processo(item_id: int, db: Session = SessionDep):
    return get_or_404(db, Processo, item_id)


@router.put("/processos/{item_id}", response_model=ProcessoRead, tags=["processos"])
def update_processo(item_id: int, payload: ProcessoUpdate, db: Session = SessionDep):
    obj = get_or_404(db, Processo, item_id)
    update_model(obj, payload)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.delete("/processos/{item_id}", status_code=204, tags=["processos"])
def delete_processo(item_id: int, db: Session = SessionDep):
    db.delete(get_or_404(db, Processo, item_id))
    commit_or_409(db)


@router.post("/contratos", response_model=ContratoRead, status_code=201, tags=["contratos"])
def create_contrato(payload: ContratoCreate, db: Session = SessionDep):
    obj = Contrato(**{k: getattr(v, "value", v) for k, v in payload.model_dump().items()})
    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.get("/contratos", response_model=list[ContratoRead], tags=["contratos"])
def list_contratos(software_id: int | None = None, status: ContratoStatus | None = None, db: Session = SessionDep):
    query = db.query(Contrato).options(selectinload(Contrato.software))
    if software_id:
        query = query.filter(Contrato.software_id == software_id)
    if status:
        query = query.filter(Contrato.status == status.value)
    return query.order_by(Contrato.vencimento_subscricao).all()


@router.get("/contratos/{item_id}", response_model=ContratoRead, tags=["contratos"])
def get_contrato(item_id: int, db: Session = SessionDep):
    obj = db.scalars(
        select(Contrato).options(selectinload(Contrato.software)).where(Contrato.id == item_id)
    ).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    return obj


@router.put("/contratos/{item_id}", response_model=ContratoRead, tags=["contratos"])
def update_contrato(item_id: int, payload: ContratoUpdate, db: Session = SessionDep):
    obj = get_or_404(db, Contrato, item_id)
    update_model(obj, payload)
    commit_or_409(db)
    db.refresh(obj)
    return obj


@router.delete("/contratos/{item_id}", status_code=204, tags=["contratos"])
def delete_contrato(item_id: int, db: Session = SessionDep):
    db.delete(get_or_404(db, Contrato, item_id))
    commit_or_409(db)


def item_query(db: Session):
    return db.query(ItemCiclo).options(*ITEM_LOADS)


@router.post("/itens", response_model=ItemCicloRead, status_code=201, tags=["itens"])
def create_item(payload: ItemCicloCreate, request: Request, db: Session = SessionDep):
    validate_item_rules(db, payload)
    data = payload.model_dump(exclude={"area_ids", "processo_ids"})
    obj = ItemCiclo(**{k: getattr(v, "value", v) for k, v in data.items()})
    db.add(obj)
    db.flush()
    apply_item_relationships(db, obj, payload.area_ids, payload.processo_ids)
    db.add(ItemHistorico(item=obj, status_novo=obj.status, usuario=current_user(request), observacao="Criacao do item"))
    commit_or_409(db)
    return item_query(db).filter(ItemCiclo.id == obj.id).one()


@router.get("/itens", response_model=list[ItemCicloRead], tags=["itens"])
def list_itens(
    ciclo_id: int | None = Query(default=None),
    ano: int | None = Query(default=None),
    semestre: Semestre | None = Query(default=None),
    software_id: int | None = Query(default=None),
    area_id: int | None = Query(default=None),
    processo: str | None = Query(default=None),
    contrato_id: int | None = Query(default=None),
    modalidade: Modalidade | None = Query(default=None),
    tipo_movimentacao: TipoMovimentacao | None = Query(default=None),
    status: ItemStatus | None = Query(default=None),
    prioridade: Prioridade | None = Query(default=None),
    vencimento_dias: int | None = Query(default=None),
    db: Session = SessionDep,
):
    query = item_query(db).join(ItemCiclo.ciclo)
    if ciclo_id:
        query = query.filter(ItemCiclo.ciclo_id == ciclo_id)
    if ano:
        query = query.filter(Ciclo.ano == ano)
    if semestre:
        query = query.filter(Ciclo.semestre == semestre.value)
    if software_id:
        query = query.filter(ItemCiclo.software_id == software_id)
    if area_id:
        query = query.join(ItemCiclo.areas).filter(Area.id == area_id)
    if processo:
        query = query.join(ItemCiclo.processos).filter(Processo.numero.ilike(f"%{processo}%"))
    if contrato_id:
        query = query.filter(ItemCiclo.contrato_id == contrato_id)
    if modalidade:
        query = query.filter(ItemCiclo.modalidade == modalidade.value)
    if tipo_movimentacao:
        query = query.filter(ItemCiclo.tipo_movimentacao == tipo_movimentacao.value)
    if status:
        query = query.filter(ItemCiclo.status == status.value)
    if prioridade:
        query = query.filter(ItemCiclo.prioridade == prioridade.value)
    if vencimento_dias:
        from datetime import date, timedelta
        query = query.filter(ItemCiclo.vencimento_subscricao <= date.today() + timedelta(days=vencimento_dias))
    return query.order_by(ItemCiclo.updated_at.desc()).all()


@router.get("/itens/{item_id}", response_model=ItemCicloRead, tags=["itens"])
def get_item(item_id: int, db: Session = SessionDep):
    obj = item_query(db).filter(ItemCiclo.id == item_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    return obj


@router.put("/itens/{item_id}", response_model=ItemCicloRead, tags=["itens"])
def update_item(item_id: int, payload: ItemCicloUpdate, request: Request, db: Session = SessionDep):
    obj = item_query(db).filter(ItemCiclo.id == item_id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    old_status = obj.status
    validate_item_rules(db, payload, obj)
    update_model(obj, payload, exclude={"area_ids", "processo_ids", "historico_observacao"})
    apply_item_relationships(db, obj, payload.area_ids, payload.processo_ids)
    if payload.status is not None and old_status != payload.status.value:
        db.add(
            ItemHistorico(
                item=obj,
                status_anterior=old_status,
                status_novo=payload.status.value,
                usuario=current_user(request),
                observacao=payload.historico_observacao,
            )
        )
    commit_or_409(db)
    return item_query(db).filter(ItemCiclo.id == item_id).one()


@router.delete("/itens/{item_id}", status_code=204, tags=["itens"])
def delete_item(item_id: int, db: Session = SessionDep):
    db.delete(get_or_404(db, ItemCiclo, item_id))
    commit_or_409(db)


@router.get("/dashboard", response_model=DashboardRead, tags=["relatorios"])
def get_dashboard(ciclo_id: int | None = None, db: Session = SessionDep):
    return dashboard(db, ciclo_id)


@router.get("/relatorios/consolidado-softwares", response_model=list[ConsolidadoSoftwareRead], tags=["relatorios"])
def relatorio_consolidado(ciclo_id: int | None = None, db: Session = SessionDep):
    return consolidated_by_software(db, ciclo_id)


@router.get("/relatorios/por-area", response_model=list[VisaoAreaRead], tags=["relatorios"])
def relatorio_area(area_id: int | None = None, db: Session = SessionDep):
    return by_area(db, area_id)


@router.get("/relatorios/vencimentos", tags=["relatorios"])
def relatorio_vencimentos(dias: int | None = Query(default=180), db: Session = SessionDep):
    return expirations(db, dias)


def response_export(rows: list[dict[str, Any]], formato: str, filename: str) -> StreamingResponse:
    if formato == "xlsx":
        content = rows_to_xlsx(rows)
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return StreamingResponse(
            BytesIO(content),
            media_type=media,
            headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
        )
    content = rows_to_csv(rows).encode("utf-8-sig")
    return StreamingResponse(
        BytesIO(content),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )


@router.get("/export/{relatorio}", tags=["exportacao"])
def export_report(relatorio: str, formato: str = Query("csv", pattern="^(csv|xlsx)$"), db: Session = SessionDep):
    if relatorio == "itens":
        rows = item_rows(item_query(db).all())
    elif relatorio == "consolidado-softwares":
        rows = consolidated_by_software(db)
    elif relatorio == "por-area":
        rows = by_area(db)
    elif relatorio == "vencimentos":
        rows = expirations(db)
    else:
        raise HTTPException(status_code=404, detail="Relatorio nao encontrado.")
    return response_export(rows, formato, relatorio)


def parse_upload_rows(file: UploadFile, content: bytes) -> Iterable[dict[str, str]]:
    if file.filename and file.filename.lower().endswith(".xlsx"):
        workbook = load_workbook(BytesIO(content), data_only=True)
        sheet = workbook.active
        headers = [str(cell.value).strip() for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            yield {headers[index]: ("" if value is None else str(value)) for index, value in enumerate(row)}
    else:
        import csv
        from io import StringIO
        yield from csv.DictReader(StringIO(content.decode("utf-8-sig")))


@router.post("/import/itens", response_model=ImportResult, tags=["importacao"])
async def import_itens(file: UploadFile = File(...), db: Session = SessionDep):
    content = await file.read()
    created = 0
    errors: list[str] = []
    for line, row in enumerate(parse_upload_rows(file, content), start=2):
        try:
            ciclo = db.query(Ciclo).filter(Ciclo.nome == row["ciclo"]).one()
            software = db.query(Software).filter(Software.nome == row["software"]).one()
            contrato = None
            if row.get("contrato"):
                contrato = db.query(Contrato).filter(Contrato.numero == row["contrato"]).one_or_none()
            areas = [a.strip() for a in row.get("areas", "").replace(";", ",").split(",") if a.strip()]
            processos = [p.strip() for p in row.get("processos_sei", "").replace(";", ",").split(",") if p.strip()]
            area_objs = db.query(Area).filter(Area.sigla.in_(areas)).all()
            processo_objs = db.query(Processo).filter(Processo.numero.in_(processos)).all()
            payload = ItemCicloCreate(
                ciclo_id=ciclo.id,
                software_id=software.id,
                tipo_movimentacao=row["tipo_movimentacao"],
                modalidade=row["modalidade"],
                contrato_id=contrato.id if contrato else None,
                vencimento_subscricao=row.get("vencimento_subscricao") or None,
                quantidade_solicitada=float(row["quantidade"]) if row.get("quantidade") else None,
                lote=row.get("lote") or None,
                observacoes=row.get("observacoes") or None,
                justificativa=row.get("observacoes") or None,
                area_ids=[area.id for area in area_objs],
                processo_ids=[processo.id for processo in processo_objs],
            )
            validate_item_rules(db, payload)
            data = payload.model_dump(exclude={"area_ids", "processo_ids"})
            item = ItemCiclo(**{k: getattr(v, "value", v) for k, v in data.items()})
            db.add(item)
            db.flush()
            apply_item_relationships(db, item, payload.area_ids, payload.processo_ids)
            db.add(ItemHistorico(item=item, status_novo=item.status, usuario="importacao"))
            created += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Linha {line}: {exc}")
    commit_or_409(db)
    return {"criados": created, "erros": errors}
