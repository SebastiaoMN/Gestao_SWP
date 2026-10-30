# Arquitetura proposta

O sistema foi iniciado como um microserviço Python com FastAPI para controlar contratos ativos de softwares de prateleira, ciclos semestrais de aquisição, solicitações, licitações e fornecedores.

## Módulos de domínio

- **Fornecedores**: cadastro de fornecedor, documento, pessoa de contato, e-mail, telefone e observações para comunicação rápida.
- **Ciclos de aquisição**: dois ciclos por ano (`first_semester` e `second_semester`) com janela de solicitação para o ciclo seguinte e data prevista de licitação.
- **Solicitações**: demandas de novas aquisições, renovações e aditivos, vinculadas ao ciclo alvo.
- **Licitações**: processos licitatórios vinculados ao ciclo e aos contratos resultantes.
- **Contratos**: contratos ativos com software, quantidade de licenças/setores, empresa, número do contrato, ciclo de contratação, valor total, data do contrato, vigência das licenças, fiscal COATEC e descrição de utilização.

## Padrões técnicos adotados

- **API-first** com FastAPI e OpenAPI automático em `/docs`.
- **Persistência relacional** com SQLModel, preparada para SQLite local e PostgreSQL em produção.
- **Autenticação federada** por Keycloak/OIDC com validação de token Bearer.
- **Logs estruturados** em JSON com `structlog`.
- **Observabilidade** com endpoint `/metrics` em formato Prometheus e health check em `/api/v1/health`.
- **Responsividade e acessibilidade** na tela inicial com HTML semântico, skip link, contraste e layout fluido.
- **Containerização** com Docker e docker-compose para API, PostgreSQL e Keycloak.

## Próximos incrementos recomendados

1. Adicionar migrações com Alembic.
2. Criar perfis e papéis no Keycloak: solicitante, gestor de contratos, comprador, auditor e administrador.
3. Implementar trilha de auditoria para alterações em solicitações, licitações e contratos.
4. Criar regras de negócio para abrir/fechar janelas de solicitação automaticamente.
5. Criar notificações de vencimento, renovação e pendências por e-mail ou mensageria.
6. Separar frontend em aplicação SPA ou server-side HTMX conforme necessidade de interação.
