"""Ivan Helpdesk API - Day 2/10: REST API with SQLAlchemy ORM."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db, init_db, Base
from models import Ticket
from schemas import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketListResponse,
    HealthResponse,
)
from service import TicketService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB on startup."""
    init_db()
    yield


app = FastAPI(
    title="Ivan Helpdesk API",
    version="0.2.0",
    description="Sistema de helpdesk para portfólio — Day 2/10: REST API + ORM",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get service instance
def get_ticket_service(db: Session = Depends(get_db)) -> TicketService:
    return TicketService(db)


# ─── Health Check ───

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    """Health check endpoint for monitoring / load balancers."""
    return HealthResponse()


# ─── Ticket Endpoints ───

@app.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tickets"],
)
def create_ticket(
    ticket_data: TicketCreate,
    service: TicketService = Depends(get_ticket_service),
):
    """Criar novo chamado."""
    try:
        ticket = service.create_ticket(ticket_data)
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tickets", response_model=TicketListResponse, tags=["Tickets"])
def list_tickets(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    status_filter: str | None = Query(None, alias="status", description="Filtrar por status"),
    category: str | None = Query(None, description="Filtrar por categoria"),
    priority: str | None = Query(None, description="Filtrar por prioridade"),
    requester_email: str | None = Query(None, description="Filtrar por email do solicitante"),
    service: TicketService = Depends(get_ticket_service),
):
    """Listar chamados com paginação e filtros."""
    return service.list_tickets(
        page=page,
        page_size=page_size,
        status=status_filter,
        category=category,
        priority=priority,
        requester_email=requester_email,
    )


@app.get("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def get_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
):
    """Obter detalhes de um chamado."""
    ticket = service.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return ticket


@app.patch("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    service: TicketService = Depends(get_ticket_service),
):
    """Atualizar chamado (parcial)."""
    try:
        ticket = service.update_ticket(ticket_id, ticket_data)
        if not ticket:
            raise HTTPException(status_code=404, detail="Chamado não encontrado")
        return ticket
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Tickets"])
def delete_ticket(
    ticket_id: int,
    service: TicketService = Depends(get_ticket_service),
):
    """Excluir chamado."""
    if not service.delete_ticket(ticket_id):
        raise HTTPException(status_code=404, detail="Chamado não encontrado")


# ─── Dashboard Stats ───

@app.get("/stats", tags=["Dashboard"])
def get_stats(service: TicketService = Depends(get_ticket_service)):
    """Estatísticas para dashboard."""
    return service.get_stats()


# ─── Root Page ───

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ivan Helpdesk API</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>* { font-family: 'Inter', sans-serif; }</style>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen flex items-center justify-center p-8">
        <div class="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 md:p-12 text-center">
            <div class="w-20 h-20 mx-auto mb-6 bg-blue-100 rounded-2xl flex items-center justify-center">
                <svg class="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
            </div>
            <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Ivan Helpdesk API</h1>
            <p class="text-gray-500 mb-8 text-lg">Sistema de chamados para portfólio de TI/Suporte/Backend</p>

            <div class="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8 text-left">
                <h2 class="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                    <span class="bg-blue-600 text-white text-xs px-2 py-0.5 rounded">Day 2/10</span>
                    Status do Projeto
                </h2>
                <ul class="space-y-2 text-sm text-blue-700">
                    <li class="flex items-center gap-2">✅ <strong>Database:</strong> SQLAlchemy + SQLite configurado</li>
                    <li class="flex items-center gap-2">✅ <strong>Dependências:</strong> FastAPI, Uvicorn, Pydantic, etc.</li>
                    <li class="flex items-center gap-2">✅ <strong>Models/Schemas:</strong> Ticket ORM + Pydantic schemas</li>
                    <li class="flex items-center gap-2">✅ <strong>CRUD API:</strong> REST completo (/tickets, /stats)</li>
                    <li class="flex items-center gap-2">⏳ <strong>Frontend SPA:</strong> Dia 4</li>
                    <li class="flex items-center gap-2">⏳ <strong>Serviço Windows:</strong> Dia 6</li>
                </ul>
            </div>

            <div class="space-y-3">
                <a href="/docs" target="_blank"
                   class="inline-block w-full py-3 px-6 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
                    📖 Ver Documentação da API (Swagger UI)
                </a>
                <a href="/health"
                   class="inline-block w-full py-3 px-6 bg-gray-100 text-gray-700 font-semibold rounded-lg hover:bg-gray-200 transition-colors">
                    🏥 Health Check
                </a>
                <a href="/stats"
                   class="inline-block w-full py-3 px-6 bg-green-100 text-green-700 font-semibold rounded-lg hover:bg-green-200 transition-colors">
                    📊 Dashboard Stats (JSON)
                </a>
            </div>

            <p class="mt-8 text-xs text-gray-400">
                Deploy local: <code class="bg-gray-100 px-1.5 py-0.5 rounded">E:\\projetos\\ivan-helpdesk\\deploy\\desktop\\</code><br>
                Repositório: <a href="https://github.com/JIvanAV/Helpdesk" class="text-blue-600 hover:underline" target="_blank">github.com/JIvanAV/Helpdesk</a>
            </p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)