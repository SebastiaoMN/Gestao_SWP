from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Semestre(StrEnum):
    PRIMEIRO = "1"
    SEGUNDO = "2"


class CicloStatus(StrEnum):
    PLANEJADO = "planejado"
    ABERTO = "aberto"
    EM_CONSOLIDACAO = "em_consolidacao"
    EM_EXECUCAO = "em_execucao"
    ENCERRADO = "encerrado"


class TipoMovimentacao(StrEnum):
    NOVO_PEDIDO = "novo_pedido"
    RENOVACAO = "renovacao"
    ADITIVO = "aditivo"
    PRORROGACAO = "prorrogacao"
    LICITACAO = "licitacao"
    CONTRATACAO_DIRETA = "contratacao_direta"
    HOMOLOGACAO = "homologacao"
    NAO_RENOVACAO = "nao_renovacao"
    CONTRATACAO_FUTURA = "contratacao_futura"
    SUBSTITUICAO = "substituicao"


class Modalidade(StrEnum):
    LICITACAO = "licitacao"
    RENOVACAO = "renovacao"
    ADITIVO = "aditivo"
    PRORROGACAO = "prorrogacao"
    CONTRATACAO_DIRETA = "contratacao_direta"
    HOMOLOGACAO_SOFTWARE_LIVRE = "homologacao_software_livre"
    NAO_CONTRATACAO = "nao_contratacao"
    A_DEFINIR = "a_definir"


class ItemStatus(StrEnum):
    CADASTRADO = "cadastrado"
    AGUARDANDO_INFORMACOES = "aguardando_informacoes"
    AGUARDANDO_PROCESSO_SEI = "aguardando_processo_sei"
    EM_ANALISE_TECNICA = "em_analise_tecnica"
    EM_ANALISE_CONTRATACAO = "em_analise_contratacao"
    EM_CONSOLIDACAO = "em_consolidacao"
    EM_INSTRUCAO_PROCESSUAL = "em_instrucao_processual"
    ENCAMINHADO_LICITACAO = "encaminhado_licitacao"
    ENCAMINHADO_RENOVACAO = "encaminhado_renovacao"
    ENCAMINHADO_ADITIVO = "encaminhado_aditivo"
    ENCAMINHADO_CONTRATACAO_DIRETA = "encaminhado_contratacao_direta"
    EM_HOMOLOGACAO = "em_homologacao"
    APROVADO = "aprovado"
    CONTRATADO = "contratado"
    RENOVADO = "renovado"
    NAO_RENOVADO = "nao_renovado"
    CANCELADO = "cancelado"
    SUSPENSO = "suspenso"
    CONCLUIDO = "concluido"


class Prioridade(StrEnum):
    CRITICA = "critica"
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class ProcessoTipo(StrEnum):
    SEI = "sei"
    DOD = "dod"
    OUTRO = "outro"


class ProcessoStatus(StrEnum):
    ABERTO = "aberto"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    ARQUIVADO = "arquivado"


class ContratoStatus(StrEnum):
    VIGENTE = "vigente"
    A_VENCER = "a_vencer"
    VENCIDO = "vencido"
    ENCERRADO = "encerrado"


item_area = Table(
    "item_area",
    Base.metadata,
    Column("item_id", ForeignKey("itens_ciclo.id", ondelete="CASCADE"), primary_key=True),
    Column("area_id", ForeignKey("areas.id", ondelete="CASCADE"), primary_key=True),
)

item_processo = Table(
    "item_processo",
    Base.metadata,
    Column("item_id", ForeignKey("itens_ciclo.id", ondelete="CASCADE"), primary_key=True),
    Column("processo_id", ForeignKey("processos.id", ondelete="CASCADE"), primary_key=True),
)


class Ciclo(Base):
    __tablename__ = "ciclos"

    id = Column(Integer, primary_key=True)
    nome = Column(String(180), nullable=False, index=True)
    ano = Column(Integer, nullable=False, index=True)
    semestre = Column(String(1), nullable=False, index=True)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    status = Column(String(40), nullable=False, default=CicloStatus.PLANEJADO)
    descricao = Column(Text)

    itens = relationship("ItemCiclo", back_populates="ciclo", cascade="all, delete-orphan")


class Software(Base):
    __tablename__ = "softwares"

    id = Column(Integer, primary_key=True)
    nome = Column(String(160), nullable=False, unique=True, index=True)
    fabricante = Column(String(160))
    categoria = Column(String(120))
    tipo_licenca = Column(String(120))
    modelo_fornecimento = Column(String(120))
    possui_representante_brasil = Column(Boolean, nullable=False, default=False)
    software_livre = Column(Boolean, nullable=False, default=False)
    observacoes = Column(Text)
    ativo = Column(Boolean, nullable=False, default=True)

    contratos = relationship("Contrato", back_populates="software")
    itens = relationship(
        "ItemCiclo", back_populates="software", foreign_keys="ItemCiclo.software_id"
    )


class Area(Base):
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True)
    sigla = Column(String(40), nullable=False, unique=True, index=True)
    nome = Column(String(180), nullable=False)
    unidade_superior = Column(String(180))
    responsavel = Column(String(160))
    email = Column(String(180))
    telefone = Column(String(60))
    ativo = Column(Boolean, nullable=False, default=True)

    itens = relationship("ItemCiclo", secondary=item_area, back_populates="areas")


class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True)
    numero = Column(String(80), nullable=False, unique=True, index=True)
    tipo = Column(String(20), nullable=False, default=ProcessoTipo.SEI)
    link = Column(String(500))
    status = Column(String(40), nullable=False, default=ProcessoStatus.ABERTO)
    observacoes = Column(Text)

    itens = relationship("ItemCiclo", secondary=item_processo, back_populates="processos")


class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True)
    numero = Column(String(80), nullable=False, unique=True, index=True)
    software_id = Column(Integer, ForeignKey("softwares.id"), nullable=False, index=True)
    fornecedor = Column(String(180), nullable=False)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    vencimento_subscricao = Column(Date)
    quantidade_contratada = Column(Float)
    valor_estimado = Column(Float)
    valor_contratado = Column(Float)
    status = Column(String(40), nullable=False, default=ContratoStatus.VIGENTE)
    observacoes = Column(Text)

    software = relationship("Software", back_populates="contratos")
    itens = relationship("ItemCiclo", back_populates="contrato")


class ItemCiclo(Base):
    __tablename__ = "itens_ciclo"
    __table_args__ = (UniqueConstraint("ciclo_id", "software_id", "lote", name="uq_item_lote"),)

    id = Column(Integer, primary_key=True)
    ciclo_id = Column(Integer, ForeignKey("ciclos.id"), nullable=False, index=True)
    software_id = Column(Integer, ForeignKey("softwares.id"), nullable=False, index=True)
    tipo_movimentacao = Column(String(60), nullable=False, index=True)
    modalidade = Column(String(80), nullable=False, index=True)
    lote = Column(String(80))
    contrato_id = Column(Integer, ForeignKey("contratos.id"), index=True)
    vencimento_subscricao = Column(Date)
    quantidade_atual = Column(Float)
    quantidade_solicitada = Column(Float)
    quantidade_adicional = Column(Float)
    unidade_medida = Column(String(80), default="licenca")
    prioridade = Column(String(20), nullable=False, default=Prioridade.MEDIA, index=True)
    status = Column(String(80), nullable=False, default=ItemStatus.CADASTRADO, index=True)
    justificativa = Column(Text)
    observacoes = Column(Text)
    risco = Column(Text)
    motivo_nao_renovacao = Column(Text)
    software_substituto_id = Column(Integer, ForeignKey("softwares.id"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    ciclo = relationship("Ciclo", back_populates="itens")
    software = relationship("Software", foreign_keys=[software_id], back_populates="itens")
    software_substituto = relationship("Software", foreign_keys=[software_substituto_id])
    contrato = relationship("Contrato", back_populates="itens")
    areas = relationship("Area", secondary=item_area, back_populates="itens")
    processos = relationship("Processo", secondary=item_processo, back_populates="itens")
    historico = relationship(
        "ItemHistorico",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="ItemHistorico.created_at",
    )


class ItemHistorico(Base):
    __tablename__ = "item_historico"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("itens_ciclo.id", ondelete="CASCADE"), nullable=False)
    status_anterior = Column(String(80))
    status_novo = Column(String(80), nullable=False)
    usuario = Column(String(120), nullable=False, default="sistema")
    observacao = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    item = relationship("ItemCiclo", back_populates="historico")
