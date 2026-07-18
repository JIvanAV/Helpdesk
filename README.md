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
- Autenticação simples de demonstração com técnico/perfil salvos no navegador
- Login demo revisado com armazenamento centralizado (`SESSION_KEYS`/`authStorage`) para facilitar manutenção futura
- Registro do técnico logado ao assumir ou atualizar chamados
- Comentários internos de técnicos anexados ao histórico do chamado
- Histórico de alterações/auditoria por chamado via endpoint `/tickets/{id}/audit` com campo alterado, valor anterior, novo valor e filtros por tipo/técnico
- Busca por título, descrição, solicitante e e-mail
- Filtros por status, categoria, prioridade e técnico responsável no dashboard
- Campo de impacto operacional (`baixo`, `medio`, `alto`, `parada_total`) separado da prioridade técnica
- Filtro e estatísticas por impacto operacional para apoiar triagem e relatórios futuros
- Atribuição de chamados para técnico responsável pela interface
- Base de conhecimento por categoria com checklists de suporte N1/N2
- Endpoint `/knowledge-base` para consultar dicas por categoria do chamado
- Botão para limpar filtros e voltar rapidamente à listagem principal
- Ordenação por prioridade para destacar chamados críticos
- Estatísticas de chamados por status, prioridade e categoria
- Tempo médio de atendimento/resolução exposto no dashboard e no endpoint `/stats`
- Feedback de atendimento em chamados resolvidos/fechados
- Classificação automática de SLA (No prazo, Atenção, Atrasado) para cada chamado
- Badge visual de SLA no dashboard e nos cartões de chamados
- Card de "Atrasados" no dashboard com contagem de tickets fora do SLA
- Cabeçalhos de segurança HTTP no frontend e API
- Tratamento padronizado para erros de validação e falhas internas
- CORS restrito aos endereços locais usados no demo
- Dockerfile e `docker-compose.yml` iniciais para executar o demo em container
- Revisão leve de qualidade para deixar API, service layer, modelos ORM e SPA mais legíveis
- Refatoração incremental em commits pequenos para simular manutenção real de um projeto em produção

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
3. Autenticação simples ✅ demo local sem senha real, com técnico/perfil salvos no navegador
4. Perfis: usuário, técnico e admin
5. Dashboard de métricas
6. Filtros por status/prioridade
7. Comentários nos chamados
8. Histórico de alterações ✅ auditoria por chamado disponível na API e na SPA
9. Dockerfile e docker-compose ✅ demo local containerizado na porta 8001
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
├── docs/                      # Documentação técnica e revisão de qualidade do projeto
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

Execute os testes de domínio do MVP a partir da raiz:

```bash
python -m pytest -v
```

Execute também os testes da API + frontend local:

```bash
cd deploy/desktop/backend
python -m pytest -q test_api_frontend.py
```

### 6. Smoke test rápido depois de iniciar o servidor

Com o backend rodando em `http://localhost:8001`, valide os principais endpoints:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/stats
curl http://localhost:8001/knowledge-base
```

Resultado esperado em `/health`:

```json
{
  "status": "healthy",
  "service": "ivan-helpdesk",
  "version": "0.3.10",
  "database": "connected"
}
```

### 7. Problemas comuns

| Sintoma | Solução |
|---|---|
| `ModuleNotFoundError: fastapi` | Instale `deploy/desktop/backend/requirements.txt` no ambiente virtual ativo |
| Porta ocupada | Troque `--port 8001` por outra porta livre, por exemplo `8002` |
| Página `/` não abre | Confirme que o comando foi executado dentro de `deploy/desktop/backend` |
| Banco com dados antigos | Use o script `deploy/desktop/backend/reset_db.py` para recriar a base de demo |

### 8. (Opcional) Build e deploy via Docker

O projeto possui um `Dockerfile` em `deploy/desktop/Dockerfile` e um `docker-compose.yml` em `deploy/desktop/docker-compose.yml` para executar a API + SPA local em container.

```bash
# Da raiz do projeto
cd deploy/desktop
docker compose up --build
```

Acesse o demo containerizado em:

| URL | Uso |
|---|---|
| http://localhost:8001/ | Interface SPA do Ivan Helpdesk |
| http://localhost:8001/docs | Swagger UI da API |
| http://localhost:8001/health | Health check usado pelo container |

Os dados SQLite do container ficam em um volume Docker nomeado:

```txt
ivan-helpdesk-data
```

Para parar sem apagar os dados:

```bash
docker compose down
```

Para recriar tudo do zero, inclusive o volume local do demo:

```bash
docker compose down -v
```

---

**Dica:** O demo local usa a porta 8001 neste README para evitar conflito com outros serviços. Se precisar mudar, use `--port <outra>` no comando do uvicorn.