# Controle de Ciclo de Contratações de Software de Prateleira

Aplicação full stack para substituir controles em planilhas no acompanhamento de ciclos de contratação, renovação, aditivo, prorrogação, homologação, não renovação e consolidação de softwares de prateleira.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy.
- Banco: SQLite em desenvolvimento, com modelos compatíveis com PostgreSQL.
- Migrações: Alembic.
- Frontend: React + TypeScript + Tailwind CSS em `frontend/`.
- Exportação: CSV e XLSX.
- Autenticação MVP: perfil simulado por header `X-User-Profile`.

## Rodar localmente

```bash
cd /home/sebastiao/Documents/DEV/Gestao_SWP/Gestao_SWP
source .venv/bin/activate
pip install -e ".[dev]"
python -m scripts.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Ou, depois que as dependências já estiverem instaladas:

```bash
./scripts/dev.sh
```

Acesse:

- Aplicação: <http://127.0.0.1:8000>
- Swagger/OpenAPI: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/api/v1/health>

## Frontend React

O código fonte fica em `frontend/`. Para desenvolver o frontend com Vite:

```bash
cd frontend
npm install
npm run dev
```

Para gerar o build que o FastAPI serve automaticamente:

```bash
cd frontend
npm run build
```

Enquanto o build não for regenerado, há uma versão estática funcional em `frontend/dist/index.html` para permitir o uso imediato da aplicação pelo FastAPI.

## Seed inicial

```bash
python -m scripts.seed
```

O seed cria dois ciclos:

- Contratação/Renovação Software de Prateleira - 1º Ciclo de 2026
- Contratação Software de Prateleira - 2º Ciclo de 2026

E softwares de exemplo: Canva, SketchUp, Adobe Creative Cloud, Adobe Acrobat Pro, Figma, LogMeIn, Genially, CapCut, Miro, V-Ray, Enscape, Lumion, Orçafascio, Dialux Pro, HandBrake, Filmora, Flickr, Linktree, Freepik, Corel Draw, Rocket.Chat e Mentimeter.

## Migrações Alembic

A configuração está em `alembic.ini` e `alembic/`. Para aplicar migrações manualmente:

```bash
alembic upgrade head
```

Em desenvolvimento, a aplicação também executa `create_all` no startup para facilitar o MVP local.

## Principais endpoints

CRUD:

- `GET/POST /api/v1/ciclos`
- `GET/POST /api/v1/softwares`
- `GET/POST /api/v1/areas`
- `GET/POST /api/v1/processos`
- `GET/POST /api/v1/contratos`
- `GET/POST /api/v1/itens`

Relatórios:

- `GET /api/v1/dashboard`
- `GET /api/v1/relatorios/consolidado-softwares`
- `GET /api/v1/relatorios/por-area`
- `GET /api/v1/relatorios/vencimentos?dias=180`

Exportação:

```bash
curl -o itens.csv "http://127.0.0.1:8000/api/v1/export/itens?formato=csv"
curl -o itens.xlsx "http://127.0.0.1:8000/api/v1/export/itens?formato=xlsx"
```

Relatórios exportáveis: `itens`, `consolidado-softwares`, `por-area`, `vencimentos`.

## Importação de itens

Endpoint:

```bash
POST /api/v1/import/itens
```

Aceita CSV ou XLSX com as colunas:

```text
ciclo,tipo_movimentacao,modalidade,software,contrato,vencimento_subscricao,areas,processos_sei,quantidade,lote,observacoes
```

Exemplo CSV:

```csv
ciclo,tipo_movimentacao,modalidade,software,contrato,vencimento_subscricao,areas,processos_sei,quantidade,lote,observacoes
Contratação/Renovação Software de Prateleira - 1º Ciclo de 2026,renovacao,renovacao,Canva,CT-2026-001,2026-07-25,"COATEC;ASCOM",SEI-2026-000001,35,Lote 1,Renovação anual
```

## Regras de negócio implementadas

- Todo item pertence a um ciclo.
- Todo item possui software.
- Todo item possui ao menos uma área.
- Item exige quantidade solicitada ou justificativa para quantidade indefinida.
- Status processuais exigem processo SEI/DOD ou justificativa.
- Contrato/subscrição vigente exige vencimento informado.
- Dashboard gera alertas de vencimento em 180, 120, 90, 60 e 30 dias.
- Itens são consolidados por software nos relatórios.
- Software livre/homologação segue fluxo de homologação.
- Item não renovado exige motivo.
- Toda alteração de status gera histórico automático.

## Qualidade

```bash
pytest
ruff check .
```
