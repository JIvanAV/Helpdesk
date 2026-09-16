# Ivan Helpdesk

API simples de Helpdesk/Service Desk usada como projeto de portfólio backend do José Ivan. O foco é registrar chamados, leads vindos do portfólio e casos de acompanhamento sem misturar testes, automações ou dados reais de clientes.

## O que o projeto demonstra

- FastAPI com rotas REST documentadas em `/docs`.
- Persistência SQLite local com SQLAlchemy.
- Modelos Pydantic para validar entrada e saída da API.
- Ingestão segura de leads do portfólio em `POST /tickets/from-portfolio`.
- Visualização HTML simples na rota `/`, com filtros por origem, status e prioridade.
- Testes automatizados para regras importantes do backend.

## Estrutura principal

```text
deploy/desktop/backend/
├── main.py                     # Rotas FastAPI e visualização HTML
├── database.py                 # Configuração SQLite local
├── models.py                   # Modelo Ticket e enums
├── schemas.py                  # Contratos Pydantic da API
├── service.py                  # Regras de criação, listagem, atualização e estatísticas
├── view_filters.py             # Filtros usados pela tela HTML
├── requirements.txt            # Dependências do backend
└── test_*.py                   # Testes unitários e de API
```

## Como rodar localmente

No Windows/Git Bash, a partir da raiz do repositório:

```bash
cd /e/github-projects/ivan-helpdesk
uv run --with-requirements deploy/desktop/backend/requirements.txt \
  uvicorn main:app --app-dir deploy/desktop/backend --host 127.0.0.1 --port 8000
```

Depois abra:

- Visualização dos casos: <http://127.0.0.1:8000/>
- Documentação Swagger: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

## Como rodar os testes

```bash
cd /e/github-projects/ivan-helpdesk
uv run --with-requirements deploy/desktop/backend/requirements.txt \
  python -m unittest discover -s deploy/desktop/backend -p 'test*.py'
```

## Endpoints principais

| Método | Rota | Uso |
| --- | --- | --- |
| `GET` | `/health` | Verificar se a API está respondendo. |
| `GET` | `/` | Abrir a visualização HTML dos casos. |
| `POST` | `/tickets` | Criar um chamado comum. |
| `GET` | `/tickets` | Listar chamados com paginação e filtros básicos. |
| `GET` | `/tickets/{id}` | Consultar um chamado específico. |
| `PUT` | `/tickets/{id}` | Atualizar status, prioridade ou responsável. |
| `DELETE` | `/tickets/{id}` | Remover um chamado. |
| `GET` | `/tickets/stats/summary` | Ver resumo por status e prioridade. |
| `POST` | `/tickets/from-portfolio` | Criar/reaproveitar chamado a partir de lead validado do portfólio. |

## Cuidados de uso

- Não commitar banco SQLite real, `.env`, tokens ou dados pessoais de clientes.
- Leads vindos de automação exigem confirmação humana antes de virar chamado.
- Casos de vaga/prospecção devem deixar claro quando a confirmação externa ainda está pendente.
- O banco local fica em `deploy/desktop/data/helpdesk.db` e pode ser recriado em ambiente de teste.
