"""Ivan Helpdesk API - REST API + local SPA frontend."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    version="0.3.0",
    description="Sistema de helpdesk para portfólio — REST API + frontend local",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

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


# ─── Local Frontend ───

@app.get("/", include_in_schema=False)
def root():
    """Serve the local portfolio SPA when available."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return HTMLResponse(
        """
        <h1>Ivan Helpdesk API</h1>
        <p>Frontend não encontrado. Acesse <a href="/docs">/docs</a>.</p>
        """,
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)