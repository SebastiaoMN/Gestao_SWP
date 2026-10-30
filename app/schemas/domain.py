from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.domain import (
    CicloStatus,
    ContratoStatus,
    ItemStatus,
    Modalidade,
    Prioridade,
    ProcessoStatus,
    ProcessoTipo,
    Semestre,
    TipoMovimentacao,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CicloBase(BaseModel):
    nome: str
    ano: int
    semestre: Semestre
    data_inicio: date
    data_fim: date
    status: CicloStatus = CicloStatus.PLANEJADO
    descricao: str | None = None


class CicloCreate(CicloBase):
    pass


class CicloUpdate(BaseModel):
    nome: str | None = None
    ano: int | None = None
    semestre: Semestre | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    status: CicloStatus | None = None
    descricao: str | None = None


class CicloRead(CicloBase, ORMModel):
    id: int


class SoftwareBase(BaseModel):
    nome: str
    fabricante: str | None = None
    categoria: str | None = None
    tipo_licenca: str | None = None
    modelo_fornecimento: str | None = None
    possui_representante_brasil: bool = False
    software_livre: bool = False
    observacoes: str | None = None
    ativo: bool = True


class SoftwareCreate(SoftwareBase):
    pass


class SoftwareUpdate(BaseModel):
    nome: str | None = None
    fabricante: str | None = None
    categoria: str | None = None
    tipo_licenca: str | None = None
    modelo_fornecimento: str | None = None
    possui_representante_brasil: bool | None = None
    software_livre: bool | None = None
    observacoes: str | None = None
    ativo: bool | None = None


class SoftwareRead(SoftwareBase, ORMModel):
    id: int


class AreaBase(BaseModel):
    sigla: str
    nome: str
    unidade_superior: str | None = None
    responsavel: str | None = None
    email: str | None = None
    telefone: str | None = None
    ativo: bool = True


class AreaCreate(AreaBase):
    pass


class AreaUpdate(BaseModel):
    sigla: str | None = None
    nome: str | None = None
    unidade_superior: str | None = None
    responsavel: str | None = None
    email: str | None = None
    telefone: str | None = None
    ativo: bool | None = None


class AreaRead(AreaBase, ORMModel):
    id: int


class ProcessoBase(BaseModel):
    numero: str
    tipo: ProcessoTipo = ProcessoTipo.SEI
    link: str | None = None
    status: ProcessoStatus = ProcessoStatus.ABERTO
    observacoes: str | None = None


class ProcessoCreate(ProcessoBase):
    pass


class ProcessoUpdate(BaseModel):
    numero: str | None = None
    tipo: ProcessoTipo | None = None
    link: str | None = None
    status: ProcessoStatus | None = None
    observacoes: str | None = None


class ProcessoRead(ProcessoBase, ORMModel):
    id: int


class ContratoBase(BaseModel):
    numero: str
    software_id: int
    fornecedor: str
    data_inicio: date
    data_fim: date
    vencimento_subscricao: date | None = None
    quantidade_contratada: float | None = None
    valor_estimado: float | None = None
    valor_contratado: float | None = None
    status: ContratoStatus = ContratoStatus.VIGENTE
    observacoes: str | None = None


class ContratoCreate(ContratoBase):
    pass


class ContratoUpdate(BaseModel):
    numero: str | None = None
    software_id: int | None = None
    fornecedor: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    vencimento_subscricao: date | None = None
    quantidade_contratada: float | None = None
    valor_estimado: float | None = None
    valor_contratado: float | None = None
    status: ContratoStatus | None = None
    observacoes: str | None = None


class ContratoRead(ContratoBase, ORMModel):
    id: int
    software: SoftwareRead | None = None


class ItemCicloBase(BaseModel):
    ciclo_id: int
    software_id: int
    tipo_movimentacao: TipoMovimentacao
    modalidade: Modalidade
    lote: str | None = None
    contrato_id: int | None = None
    vencimento_subscricao: date | None = None
    quantidade_atual: float | None = None
    quantidade_solicitada: float | None = None
    quantidade_adicional: float | None = None
    unidade_medida: str | None = "licenca"
    prioridade: Prioridade = Prioridade.MEDIA
    status: ItemStatus = ItemStatus.CADASTRADO
    justificativa: str | None = None
    observacoes: str | None = None
    risco: str | None = None
    motivo_nao_renovacao: str | None = None
    software_substituto_id: int | None = None
    area_ids: list[int]
    processo_ids: list[int] = []

    @field_validator("area_ids")
    @classmethod
    def at_least_one_area(cls, value: list[int]) -> list[int]:
        if not value:
            raise ValueError("Informe ao menos uma area vinculada ao item.")
        return value


class ItemCicloCreate(ItemCicloBase):
    pass


class ItemCicloUpdate(BaseModel):
    ciclo_id: int | None = None
    software_id: int | None = None
    tipo_movimentacao: TipoMovimentacao | None = None
    modalidade: Modalidade | None = None
    lote: str | None = None
    contrato_id: int | None = None
    vencimento_subscricao: date | None = None
    quantidade_atual: float | None = None
    quantidade_solicitada: float | None = None
    quantidade_adicional: float | None = None
    unidade_medida: str | None = None
    prioridade: Prioridade | None = None
    status: ItemStatus | None = None
    justificativa: str | None = None
    observacoes: str | None = None
    risco: str | None = None
    motivo_nao_renovacao: str | None = None
    software_substituto_id: int | None = None
    area_ids: list[int] | None = None
    processo_ids: list[int] | None = None
    historico_observacao: str | None = None


class ItemHistoricoRead(ORMModel):
    id: int
    item_id: int
    status_anterior: str | None = None
    status_novo: str
    usuario: str
    observacao: str | None = None
    created_at: datetime


class ItemCicloRead(ORMModel):
    id: int
    ciclo_id: int
    software_id: int
    tipo_movimentacao: str
    modalidade: str
    lote: str | None = None
    contrato_id: int | None = None
    vencimento_subscricao: date | None = None
    quantidade_atual: float | None = None
    quantidade_solicitada: float | None = None
    quantidade_adicional: float | None = None
    unidade_medida: str | None = None
    prioridade: str
    status: str
    justificativa: str | None = None
    observacoes: str | None = None
    risco: str | None = None
    motivo_nao_renovacao: str | None = None
    software_substituto_id: int | None = None
    created_at: datetime
    updated_at: datetime
    ciclo: CicloRead | None = None
    software: SoftwareRead | None = None
    contrato: ContratoRead | None = None
    areas: list[AreaRead] = []
    processos: list[ProcessoRead] = []
    historico: list[ItemHistoricoRead] = []


class DashboardRead(BaseModel):
    total_itens: int
    total_softwares_distintos: int
    por_status: dict[str, int]
    por_modalidade: dict[str, int]
    por_prioridade: dict[str, int]
    vencimentos: dict[str, int]
    vencidos: int
    itens_sem_processo_sei: int
    itens_sem_quantidade_definida: int


class ConsolidadoSoftwareRead(BaseModel):
    software_id: int
    software: str
    quantidade_solicitada: float
    quantidade_adicional: float
    areas: list[str]
    processos: list[str]
    contratos: list[str]
    vencimentos: list[date]


class VisaoAreaRead(BaseModel):
    area_id: int
    sigla: str
    area: str
    software: str
    quantidade_solicitada: float | None = None
    processo: str | None = None
    status: str
    modalidade: str


class ImportResult(BaseModel):
    criados: int
    erros: list[str]
