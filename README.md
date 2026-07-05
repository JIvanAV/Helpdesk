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
- Filtros por status, categoria, prioridade e técnico responsável no dashboard
- Atribuição de chamados para técnico responsável pela interface
- Base de conhecimento por categoria com checklists de suporte N1/N2
- Endpoint `/knowledge-base` para consultar dicas por categoria do chamado
- Botão para limpar filtros e voltar rapidamente à listagem principal
- Ordenação por prioridade para destacar chamados críticos
- Estatísticas de chamados por status, prioridade e categoria
- Feedback de atendimento em chamados resolvidos/fechados
- Cabeçalhos de segurança HTTP no frontend e API
- Tratamento padronizado para erros de validação e falhas internas
- CORS restrito aos endereços locais usados no demo

## MVP inicial

- Cadastro de chamados em memória
- Listagem de chamados
- Atualização de status
- Regras básicas de prioridade
- Testes unitários do domínio
- Higienização de dados sensíveis em chamados (senhas/tokens redigidos)
- Limites de tamanho para campos controlados pelo usuário

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

| Ferramenta | Versão/uso |
|---|---|
| Python | 3.11 ou superior |
| Git | Clonar o repositório e versionar mudanças |
| Navegador | Acessar a SPA local e a documentação Swagger |
| Docker | Opcional, apenas para futuro deploy containerizado |

### Estrutura principal

```txt
Helpdesk/
├── deploy/desktop/backend/    # API FastAPI, SQLite, testes de integração
├── deploy/desktop/frontend/   # SPA local em HTML/Alpine.js
├── deploy/desktop/data/       # Banco SQLite local de demonstração
├── docs/                      # Documentação técnica do projeto
└── tests/                     # Testes de domínio do MVP
```

### 1. Clone o repositório

```bash
git clone https://github.com/JIvanAV/Helpdesk.git
cd Helpdesk
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

# Git Bash no Windows, Linux ou macOS
python -m venv .venv
source .venv/Scripts/activate  # Windows/Git Bash
# source .venv/bin/activate    # Linux/macOS
```

### 3. Instale as dependências do backend

O backend desktop possui dependências próprias em `deploy/desktop/backend/requirements.txt`.

```bash
python -m pip install --upgrade pip
python -m pip install -r deploy/desktop/backend/requirements.txt
```

Se preferir usar `uv`:

```bash
uv pip install -r deploy/desktop/backend/requirements.txt
```

### 4. Rode o backend e a interface local

```bash
cd deploy/desktop/backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

Acesse:

| URL | Uso |
|---|---|
| http://localhost:8001/ | Interface SPA do Ivan Helpdesk |
| http://localhost:8001/docs | Swagger UI da API |
| http://localhost:8001/health | Verificação rápida da API |
| http://localhost:8001/stats | Métricas do dashboard |

A base de conhecimento também fica disponível pela API:

```bash
curl http://localhost:8001/knowledge-base
curl http://localhost:8001/knowledge-base/network
```

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