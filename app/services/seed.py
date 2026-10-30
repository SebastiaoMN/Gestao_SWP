from datetime import date, timedelta

from sqlalchemy.orm import Session

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

SOFTWARES = [
    "Canva",
    "SketchUp",
    "Adobe Creative Cloud",
    "Adobe Acrobat Pro",
    "Figma",
    "LogMeIn",
    "Genially",
    "CapCut",
    "Miro",
    "V-Ray",
    "Enscape",
    "Lumion",
    "Orçafascio",
    "Dialux Pro",
    "HandBrake",
    "Filmora",
    "Flickr",
    "Linktree",
    "Freepik",
    "Corel Draw",
    "Rocket.Chat",
    "Mentimeter",
]


def run_seed(db: Session) -> dict[str, int]:
    if db.query(Ciclo).count() > 0:
        return {"ciclos": db.query(Ciclo).count(), "softwares": db.query(Software).count()}

    ciclos = [
        Ciclo(
            nome="Contratação/Renovação Software de Prateleira - 1º Ciclo de 2026",
            ano=2026,
            semestre=Semestre.PRIMEIRO.value,
            data_inicio=date(2026, 1, 2),
            data_fim=date(2026, 6, 30),
            status=CicloStatus.ABERTO.value,
            descricao="Ciclo dedicado a renovacoes, aditivos, prorrogacoes e novas demandas priorizadas.",
        ),
        Ciclo(
            nome="Contratação Software de Prateleira - 2º Ciclo de 2026",
            ano=2026,
            semestre=Semestre.SEGUNDO.value,
            data_inicio=date(2026, 7, 1),
            data_fim=date(2026, 12, 18),
            status=CicloStatus.PLANEJADO.value,
            descricao="Ciclo para consolidacao de novas contratacoes e homologacoes.",
        ),
    ]
    db.add_all(ciclos)

    areas = [
        Area(sigla="COATEC", nome="Coordenadoria de Apoio Tecnico", responsavel="Maria Silva", email="coatec@example.local"),
        Area(sigla="ASCOM", nome="Assessoria de Comunicacao", responsavel="Joao Pereira", email="ascom@example.local"),
        Area(sigla="DENGEP", nome="Diretoria de Engenharia", responsavel="Ana Costa", email="dengep@example.local"),
        Area(sigla="DITEC", nome="Diretoria de Tecnologia", responsavel="Carlos Lima", email="ditec@example.local"),
    ]
    db.add_all(areas)

    softwares = []
    for name in SOFTWARES:
        softwares.append(
            Software(
                nome=name,
                fabricante=name.split()[0],
                categoria="Produtividade" if name in {"Canva", "Figma", "Miro", "Mentimeter"} else "Especializado",
                tipo_licenca="Assinatura",
                modelo_fornecimento="SaaS" if name not in {"SketchUp", "V-Ray", "Lumion"} else "Licenca nomeada",
                possui_representante_brasil=name not in {"HandBrake", "Rocket.Chat"},
                software_livre=name in {"HandBrake", "Rocket.Chat"},
                ativo=True,
            )
        )
    db.add_all(softwares)
    db.flush()

    processos = [
        Processo(numero="SEI-2026-000001", tipo=ProcessoTipo.SEI.value, status=ProcessoStatus.EM_ANDAMENTO.value),
        Processo(numero="SEI-2026-000002", tipo=ProcessoTipo.SEI.value, status=ProcessoStatus.ABERTO.value),
        Processo(numero="DOD-2026-0003", tipo=ProcessoTipo.DOD.value, status=ProcessoStatus.ABERTO.value),
    ]
    db.add_all(processos)
    db.flush()

    contracts = []
    for index, software in enumerate(softwares[:8], start=1):
        contracts.append(
            Contrato(
                numero=f"CT-2026-{index:03d}",
                software_id=software.id,
                fornecedor=f"Fornecedor {software.nome}",
                data_inicio=date(2026, 1, 1),
                data_fim=date(2026, 12, 31),
                vencimento_subscricao=date.today() + timedelta(days=30 * index),
                quantidade_contratada=20 + index,
                valor_estimado=10000 * index,
                valor_contratado=9200 * index,
                status=ContratoStatus.VIGENTE.value,
            )
        )
    db.add_all(contracts)
    db.flush()

    items = [
        ItemCiclo(
            ciclo_id=ciclos[0].id,
            software_id=softwares[0].id,
            tipo_movimentacao=TipoMovimentacao.RENOVACAO.value,
            modalidade=Modalidade.RENOVACAO.value,
            contrato_id=contracts[0].id,
            vencimento_subscricao=contracts[0].vencimento_subscricao,
            quantidade_atual=20,
            quantidade_solicitada=35,
            quantidade_adicional=15,
            unidade_medida="licenca",
            prioridade=Prioridade.ALTA.value,
            status=ItemStatus.EM_INSTRUCAO_PROCESSUAL.value,
            justificativa="Renovacao necessaria para continuidade dos servicos.",
            observacoes="Consolidar demanda da ASCOM e COATEC.",
        ),
        ItemCiclo(
            ciclo_id=ciclos[0].id,
            software_id=softwares[2].id,
            tipo_movimentacao=TipoMovimentacao.ADITIVO.value,
            modalidade=Modalidade.ADITIVO.value,
            contrato_id=contracts[2].id,
            vencimento_subscricao=contracts[2].vencimento_subscricao,
            quantidade_atual=40,
            quantidade_solicitada=50,
            quantidade_adicional=10,
            unidade_medida="licenca",
            prioridade=Prioridade.CRITICA.value,
            status=ItemStatus.ENCAMINHADO_ADITIVO.value,
            justificativa="Crescimento de demanda nas unidades de comunicacao.",
        ),
        ItemCiclo(
            ciclo_id=ciclos[1].id,
            software_id=softwares[14].id,
            tipo_movimentacao=TipoMovimentacao.HOMOLOGACAO.value,
            modalidade=Modalidade.HOMOLOGACAO_SOFTWARE_LIVRE.value,
            quantidade_solicitada=None,
            unidade_medida="instalacao",
            prioridade=Prioridade.MEDIA.value,
            status=ItemStatus.EM_HOMOLOGACAO.value,
            justificativa="Software livre em homologacao, sem quantidade fechada.",
        ),
    ]
    db.add_all(items)
    db.flush()
    items[0].areas = [areas[0], areas[1]]
    items[0].processos = [processos[0]]
    items[1].areas = [areas[1], areas[3]]
    items[1].processos = [processos[1]]
    items[2].areas = [areas[3]]
    items[2].processos = [processos[2]]
    for item in items:
        db.add(ItemHistorico(item=item, status_novo=item.status, usuario="seed"))
    db.commit()
    return {"ciclos": len(ciclos), "softwares": len(softwares), "itens": len(items)}
