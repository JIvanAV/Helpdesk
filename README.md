# Ivan Helpdesk

Sistema de helpdesk em construção diária para portfólio de TI, suporte e desenvolvimento backend.

## Objetivo

Criar um sistema simples, evolutivo e demonstrável para registrar chamados, acompanhar status, priorizar atendimentos e mostrar habilidades práticas de:

- Suporte técnico e infraestrutura
- Backend Python/FastAPI
- APIs REST
- Organização de regras de negócio
- Testes automatizados
- Evolução diária via GitHub

## Melhorias já implementadas

- API REST com FastAPI e persistência SQLite local
- Frontend SPA local para abrir, listar e atualizar chamados
- Busca por título, descrição, solicitante e e-mail
- Filtros por status e categoria no dashboard
- Ordenação por prioridade para destacar chamados críticos
- Estatísticas de chamados por status, prioridade e categoria
- Feedback de atendimento em chamados resolvidos/fechados

## MVP inicial

- Cadastro de chamados em memória
- Listagem de chamados
- Atualização de status
- Regras básicas de prioridade
- Testes unitários do domínio

## Roadmap diário sugerido

1. Persistência com SQLite
2. API REST com FastAPI
3. Autenticação simples
4. Perfis: usuário, técnico e admin
5. Dashboard de métricas
6. Filtros por status/prioridade
7. Comentários nos chamados
8. Histórico de alterações
9. Dockerfile e docker-compose
10. CI com GitHub Actions

## Como rodar o aplicativo no seu PC

### Pré-requisitos
- Python 3.11+
- Git
- (Opcional) Docker para deploy containerizado

### 1. Clone o repositório
```bash
git clone https://github.com/JIvanAV/ivan-helpdesk.git
cd ivan-helpdesk
```

### 2. Crie e ative o ambiente virtual
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/macOS / Git Bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -e ".[dev]"
# ou usando uv (mais rápido):
uv sync --dev
```

### 4. Rode o backend (API FastAPI)
```bash
# Modo desenvolvimento (hot reload)
cd deploy/desktop/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Acesse: http://localhost:8000/docs (Swagger UI)

### 5. Rode os testes
```bash
# Da raiz do projeto
pytest -v
# Com coverage
pytest --cov=src --cov-report=term-missing
```

### 6. (Opcional) Build e deploy via Docker
```bash
# Da raiz do projeto
docker compose -f deploy/desktop/docker-compose.yml up --build
```

---

**Dica:** O backend roda na porta 8000 por padrão. Se precisar mudar, use `--port <outra>` no comando do uvicorn.