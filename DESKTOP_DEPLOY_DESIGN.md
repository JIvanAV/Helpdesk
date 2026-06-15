# Ivan Helpdesk — Desktop Deploy Design
**Objetivo**: Versão rodando local no desktop (Windows) e acessível via navegador para demonstrações ao vivo (entrevistas, portfólio, stakeholders).

---

## 1. Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────┐
│                        DESKTOP (Windows)                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │◄───│   Backend    │◄───│   Database   │  │
│  │  (HTML/JS)   │    │  (FastAPI)   │    │  (SQLite)    │  │
│  │  Port: 8080  │    │  Port: 8000  │    │  file: *.db  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │            │
│         └───────────────────┼───────────────────┘            │
│                             ▼                                 │
│                    ┌──────────────┐                          │
│                    │  Process     │                          │
│                    │  Manager     │                          │
│                    │  (systemd/   │                          │
│                    │   NSSM/      │                          │
│                    │   PM2)       │                          │
│                    └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| **API** | FastAPI + Uvicorn | Python nativo, async, OpenAPI automático, leve |
| **DB** | SQLite (arquivo único) | Zero config, portável, roda no Windows sem Docker |
| **Frontend** | HTML5 + Alpine.js + Tailwind (CDN) | Zero build, ~15KB, reativo simples, bonito out-of-the-box |
| **Servidor estático** | FastAPI `StaticFiles` ou Python `http.server` | Mesmo processo ou separado na porta 8080 |
| **Process Manager** | NSSM (Non-Sucking Service Manager) | Instala como serviço Windows, auto-start, logs |
| **Tunnel público (demo)** | Cloudflare Tunnel `cloudflared` | HTTPS público grátis, sem abrir porta no roteador |

---

## 3. Estrutura de Pastas (Produção no Desktop)

```
E:\helpdesk-demo\                    ← Raiz do deploy (HD 360GB)
├── backend/
│   ├── main.py                      ← FastAPI app entrypoint
│   ├── domain.py                    ← Modelos (já existe)
│   ├── service.py                   ← Service com SQLite
│   ├── database.py                  ← SQLAlchemy + SQLite
│   ├── schemas.py                   ← Pydantic models
│   ├── auth.py                      ← JWT simples (opcional)
│   ├── requirements.txt
│   └── .env                         ← Configs locais (SECRET_KEY, etc)
├── frontend/
│   ├── index.html                   ← SPA single-file
│   └── assets/                      ← (opcional: favicon, logo)
├── data/
│   └── helpdesk.db                  ← SQLite persistido
├── logs/
│   ├── backend.log
│   └── frontend.log
├── scripts/
│   ├── install_service.bat          ← Instala como serviço Windows
│   ├── uninstall_service.bat
│   ├── start_dev.bat                ← Dev mode (dois terminais)
│   └── health_check.py              ← Verifica se API responde
├── cloudflared/                     ← Para demo pública
│   ├── config.yml
│   └── cloudflared.exe
└── README_DEPLOY.md
```

---

## 4. Backend — FastAPI + SQLite

### `requirements.txt`
```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy==2.0.36
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
alembic==1.13.3          # migrações (opcional, mas recomendado)
```

### `database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "helpdesk.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},  # SQLite + FastAPI
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `service.py` — Adaptação do `HelpdeskService` para SQLAlchemy
```python
from sqlalchemy.orm import Session
from sqlalchemy import select
from .domain import Ticket, TicketStatus, TicketPriority
from .schemas import TicketCreate, TicketUpdate

class TicketService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: TicketCreate) -> Ticket:
        ticket = Ticket(**data.model_dump())
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def list(self, status: TicketStatus | None = None,
             priority: TicketPriority | None = None) -> list[Ticket]:
        stmt = select(Ticket)
        if status:
            stmt = stmt.where(Ticket.status == status)
        if priority:
            stmt = stmt.where(Ticket.priority == priority)
        return self.db.execute(stmt.order_by(Ticket.id)).scalars().all()

    def get(self, ticket_id: int) -> Ticket | None:
        return self.db.get(Ticket, ticket_id)

    def update_status(self, ticket_id: int, status: TicketStatus) -> Ticket:
        ticket = self.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket não encontrado")
        if ticket.status == TicketStatus.CLOSED and status != TicketStatus.CLOSED:
            raise ValueError("Chamados fechados não podem ser reabertos")
        ticket.status = status
        ticket.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def summary(self) -> dict[str, int]:
        from sqlalchemy import func
        stmt = select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
        return {row[0].value: row[1] for row in self.db.execute(stmt)}
```

### `main.py` — Entrypoint
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path

from .database import Base, engine, get_db
from .service import TicketService
from .schemas import TicketCreate, TicketUpdate, TicketOut
from .domain import TicketStatus, TicketPriority

# Cria tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ivan Helpdesk API", version="0.1.0")

# CORS para frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas API
@app.post("/api/tickets", response_model=TicketOut, status_code=201)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    return TicketService(db).create(payload)

@app.get("/api/tickets", response_model=list[TicketOut])
def list_tickets(status: TicketStatus | None = None,
                 priority: TicketPriority | None = None,
                 db: Session = Depends(get_db)):
    return TicketService(db).list(status=status, priority=priority)

@app.get("/api/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = TicketService(db).get(ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket não encontrado")
    return ticket

@app.patch("/api/tickets/{ticket_id}/status", response_model=TicketOut)
def update_status(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    try:
        return TicketService(db).update_status(ticket_id, payload.status)
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.get("/api/summary")
def summary(db: Session = Depends(get_db)):
    return TicketService(db).summary()

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}

# Servir frontend estático (build ou arquivo único)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
```

---

## 5. Frontend — SPA Single-File (`frontend/index.html`)

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ivan Helpdesk — Demo</title>
  <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { font-family: 'Inter', sans-serif; }
    .priority-critical { border-left: 4px solid #dc2626; }
    .priority-high { border-left: 4px solid #ea580c; }
    .priority-medium { border-left: 4px solid #d97706; }
    .priority-low { border-left: 4px solid #16a34a; }
    .status-open { background: #eff6ff; }
    .status-in_progress { background: #fffbeb; }
    .status-resolved { background: #f0fdf4; }
    .status-closed { background: #f5f5f5; opacity: 0.7; }
  </style>
</head>
<body class="bg-gray-50 min-h-screen" x-data="app()" x-init="load()">
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header -->
    <header class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 flex items-center gap-3">
        <svg class="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        Ivan Helpdesk
      </h1>
      <p class="text-gray-500 mt-1">Sistema de chamados — Demo local para portfólio</p>
    </header>

    <!-- Resumo -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6" x-show="summary">
      <template x-for="(count, status) in Object.entries(summary)" :key="status">
        <div class="bg-white rounded-lg shadow p-4 border-l-4"
             :class="['priority-' + status.replace('_', '-')]">
          <p class="text-sm text-gray-500 capitalize" x-text="status.replace('_', ' ')"></p>
          <p class="text-2xl font-bold text-gray-900" x-text="count"></p>
        </div>
      </template>
    </div>

    <!-- Novo Chamado -->
    <div class="bg-white rounded-lg shadow p-6 mb-6" x-show="showForm">
      <h2 class="text-xl font-semibold mb-4">Novo Chamado</h2>
      <form @submit.prevent="createTicket" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Título *</label>
          <input type="text" x-model="form.title" required
                 class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Descrição *</label>
          <textarea x-model="form.description" rows="3" required
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Solicitante *</label>
            <input type="text" x-model="form.requester" required
                   class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Prioridade</label>
            <select x-model="form.priority"
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option value="low">Baixa</option>
              <option value="medium" selected>Média</option>
              <option value="high">Alta</option>
              <option value="critical">Crítica</option>
            </select>
          </div>
        </div>
        <button type="submit" :disabled="loading"
                class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
          <span x-show="!loading">Criar Chamado</span>
          <span x-show="loading" class="flex items-center justify-center gap-2">
            <svg class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
            Criando...
          </span>
        </button>
      </form>
    </div>

    <!-- Lista de Chamados -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="p-4 border-b border-gray-200 flex items-center justify-between">
        <h2 class="text-xl font-semibold">Chamados</h2>
        <div class="flex gap-2">
          <select x-model="filterStatus" @change="loadTickets"
                  class="px-3 py-1 border border-gray-300 rounded-lg text-sm">
            <option value="">Todos status</option>
            <option value="open">Aberto</option>
            <option value="in_progress">Em andamento</option>
            <option value="resolved">Resolvido</option>
            <option value="closed">Fechado</option>
          </select>
          <select x-model="filterPriority" @change="loadTickets"
                  class="px-3 py-1 border border-gray-300 rounded-lg text-sm">
            <option value="">Todas prioridades</option>
            <option value="low">Baixa</option>
            <option value="medium">Média</option>
            <option value="high">Alta</option>
            <option value="critical">Crítica</option>
          </select>
        </div>
      </div>

      <div class="divide-y divide-gray-200" x-show="tickets.length > 0">
        <template x-for="ticket in tickets" :key="ticket.id">
          <div class="p-4 hover:bg-gray-50 transition-colors"
               :class="['status-' + ticket.status, 'priority-' + ticket.priority]">
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-3 mb-1">
                  <h3 class="font-medium text-gray-900 truncate" x-text="ticket.title"></h3>
                  <span class="px-2 py-0.5 text-xs font-medium rounded-full"
                      :class="priorityClass(ticket.priority)"
                      x-text="priorityLabel(ticket.priority)"></span>
                  <span class="px-2 py-0.5 text-xs font-medium rounded-full"
                      :class="statusClass(ticket.status)"
                      x-text="statusLabel(ticket.status)"></span>
                </div>
                <p class="text-gray-600 text-sm line-clamp-2" x-text="ticket.description"></p>
                <div class="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span>👤 <span x-text="ticket.requester"></span></span>
                  <span>🕐 <span x-text="formatDate(ticket.created_at)"></span></span>
                  <span>🆔 #<span x-text="ticket.id"></span></span>
                </div>
              </div>
              <div class="flex flex-col gap-2 ml-4 shrink-0">
                <select x-model="ticket.status" @change="updateStatus(ticket)"
                        :class="statusClass(ticket.status) + ' px-2 py-1 text-xs rounded border'">
                  <option value="open">Aberto</option>
                  <option value="in_progress">Em andamento</option>
                  <option value="resolved">Resolvido</option>
                  <option value="closed">Fechado</option>
                </select>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="p-8 text-center text-gray-500" x-show="tickets.length === 0 && !loading">
        Nenhum chamado encontrado. Crie o primeiro acima! 🎫
      </div>
    </div>

    <!-- Footer -->
    <footer class="mt-8 text-center text-sm text-gray-400">
      <p>Ivan Helpdesk v0.1.0 — Demo para portfólio | <a href="http://localhost:8000/docs" target="_blank" class="text-blue-600 hover:underline">API Docs (Swagger)</a></p>
    </footer>
  </div>

  <script>
    function app() {
      return {
        tickets: [],
        summary: {},
        filterStatus: '',
        filterPriority: '',
        showForm: true,
        form: { title: '', description: '', requester: '', priority: 'medium' },
        loading: false,
        API: 'http://localhost:8000',

        async load() {
          await Promise.all([this.loadTickets(), this.loadSummary()]);
        },

        async loadTickets() {
          const params = new URLSearchParams();
          if (this.filterStatus) params.set('status', this.filterStatus);
          if (this.filterPriority) params.set('priority', this.filterPriority);
          const res = await fetch(`${this.API}/api/tickets?${params}`);
          this.tickets = await res.json();
        },

        async loadSummary() {
          const res = await fetch(`${this.API}/api/summary`);
          this.summary = await res.json();
        },

        async createTicket() {
          this.loading = true;
          try {
            const res = await fetch(`${this.API}/api/tickets`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(this.form)
            });
            if (res.ok) {
              this.form = { title: '', description: '', requester: '', priority: 'medium' };
              await Promise.all([this.loadTickets(), this.loadSummary()]);
            }
          } finally {
            this.loading = false;
          }
        },

        async updateStatus(ticket) {
          await fetch(`${this.API}/api/tickets/${ticket.id}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: ticket.status })
          });
          await this.loadSummary();
        },

        priorityClass(p) {
          const map = { low: 'bg-green-100 text-green-800', medium: 'bg-yellow-100 text-yellow-800',
                        high: 'bg-orange-100 text-orange-800', critical: 'bg-red-100 text-red-800' };
          return map[p] || 'bg-gray-100 text-gray-800';
        },
        priorityLabel(p) { return p.charAt(0).toUpperCase() + p.slice(1); },

        statusClass(s) {
          const map = { open: 'bg-blue-100 text-blue-800', in_progress: 'bg-yellow-100 text-yellow-800',
                        resolved: 'bg-green-100 text-green-800', closed: 'bg-gray-100 text-gray-800' };
          return map[s] || 'bg-gray-100 text-gray-800';
        },
        statusLabel(s) { return s.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()); },

        formatDate(iso) {
          return new Date(iso).toLocaleString('pt-BR', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
          });
        }
      }
    }
  </script>
</body>
</html>
```

---

## 6. Serviço Windows (NSSM) — Auto-start + Logs

### `scripts/install_service.bat`
```bat
@echo off
REM Instala backend como serviço Windows
set SERVICE_NAME=IvanHelpdeskAPI
set PYTHON=%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe
set APP_DIR=E:\helpdesk-demo\backend
set VENV=%APP_DIR\.venv\Scripts\python.exe

REM Usa venv se existir, senão python global
if exist "%VENV%" (set PYTHON_EXE=%VENV%) else (set PYTHON_EXE=%PYTHON%)

nssm install %SERVICE_NAME% "%PYTHON_EXE%" -m uvicorn main:app --host 0.0.0.0 --port 8000
nssm set %SERVICE_NAME% AppDirectory "%APP_DIR%"
nssm set %SERVICE_NAME% AppStdout "%APP_DIR%\..\logs\backend.log"
nssm set %SERVICE_NAME% AppStderr "%APP_DIR%\..\logs\backend.log"
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateBytes 10485760
nssm set %SERVICE_NAME% Description "Ivan Helpdesk API - Demo local para portfólio"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START
nssm start %SERVICE_NAME%

echo Serviço %SERVICE_NAME% instalado e iniciado.
pause
```

### `scripts/uninstall_service.bat`
```bat
@echo off
nssm stop IvanHelpdeskAPI
nssm remove IvanHelpdeskAPI confirm
echo Serviço removido.
pause
```

---

## 7. Cloudflare Tunnel — Demo Pública (HTTPS Grátis)

### `cloudflared/config.yml`
```yaml
tunnel: ivan-helpdesk-demo
credentials-file: /path/to/tunnel-credentials.json

ingress:
  - hostname: helpdesk-ivan.trycloudflare.com
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

### Uso rápido (sem config persistente):
```bat
REM Baixe cloudflared.exe para cloudflared/
cloudflared.exe tunnel --url http://localhost:8000
```
Resultado: `https://random-name.trycloudflare.com` — compartilhe esse link na entrevista.

---

## 8. Scripts de Desenvolvimento

### `scripts/start_dev.bat`
```bat
@echo off
echo Iniciando Backend (porta 8000)...
start "Backend" cmd /k "cd /d E:\helpdesk-demo\backend && .venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Iniciando Frontend (porta 8080)...
start "Frontend" cmd /k "cd /d E:\helpdesk-demo\frontend && python -m http.server 8080"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8080
echo API Docs: http://localhost:8000/docs
pause
```

### `scripts/health_check.py`
```python
#!/usr/bin/env python3
import sys, requests
try:
    r = requests.get("http://localhost:8000/health", timeout=3)
    if r.status_code == 200 and r.json().get("status") == "ok":
        print("OK - API respondendo")
        sys.exit(0)
except Exception as e:
    print(f"FAIL - {e}")
    sys.exit(1)
```
Use no NSSM `AppExit` ou agende no Task Scheduler para monitorar.

---

## 9. Checklist de Entrega (Definição de Pronto)

- [ ] Backend FastAPI roda em `http://localhost:8000`
- [ ] Frontend abre em `http://localhost:8080` (ou servido pelo FastAPI)
- [ ] CRUD de chamados funciona end-to-end
- [ ] SQLite persiste em `E:\helpdesk-demo\data\helpdesk.db`
- [ ] Serviço Windows instalado (NSSM) — sobrevive a reboot
- [ ] Logs rotacionados em `E:\helpdesk-demo\logs\`
- [ ] `cloudflared` gera URL HTTPS pública para demo remota
- [ ] Swagger docs em `/docs` acessíveis
- [ ] Testes automatizados (`pytest`) passam
- [ ] README_DEPLOY.md com instruções de install/uninstall/start

---

## 10. Próximos Passos (Roadmap de Implementação Diária)

| Dia | Tarefa | Commit sugerido |
|-----|--------|-----------------|
| 1 | Estrutura de pastas + `requirements.txt` + `database.py` | `chore: add backend skeleton with SQLAlchemy` |
| 2 | `service.py` + `schemas.py` + migração do domínio | `feat: ticket service with SQLite persistence` |
| 3 | `main.py` com rotas CRUD + health + CORS | `feat: REST API endpoints for tickets` |
| 4 | Frontend `index.html` (Alpine + Tailwind CDN) | `feat: SPA frontend for demo` |
| 5 | Servir estático no FastAPI + ajustes de integração | `feat: serve frontend from FastAPI` |
| 6 | Scripts NSSM (install/uninstall) + logs | `chore: Windows service scripts via NSSM` |
| 7 | Cloudflare Tunnel + health check + README_DEPLOY | `docs: deploy guide + public tunnel setup` |
| 8 | Testes de integração (pytest + httpx) | `test: API integration tests` |
| 9 | Autenticação simples (JWT) — opcional para demo | `feat: simple JWT auth for multi-user demo` |
| 10 | Dashboard de métricas (gráficos com Chart.js CDN) | `feat: metrics dashboard` |

---

## 11. Variáveis de Ambiente (`.env` no backend)

```env
# Segurança
SECRET_KEY=gere-com-openssl-rand-base64-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Banco
DATABASE_URL=sqlite:///../data/helpdesk.db

# CORS (ajuste se frontend em porta/origem diferente)
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Ambiente
ENVIRONMENT=development
```

---

## 12. Comando Único para Subir Tudo (Dev)

```bat
cd E:\helpdesk-demo\backend
.venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Em outro terminal:
```bat
cd E:\helpdesk-demo\frontend
python -m http.server 8080
```
Acesse: **http://localhost:8080** (frontend) | **http://localhost:8000/docs** (Swagger)

---

**Pronto para implementar no ritmo diário (1 commit/dia). Quer que eu comece pelo Dia 1 agora?**