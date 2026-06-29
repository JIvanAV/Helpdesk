"""Ivan Helpdesk API - REST API + local SPA frontend."""

from contextlib import asynccontextmanager
from pathlib import Path
import csv
import io

from uuid import uuid4

from fastapi import FastAPI, Depends, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db, init_db
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
    version="0.3.4",
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
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Apply basic browser security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return predictable 422 errors without leaking internal validation traces."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "detail": "Verifique os campos enviados e tente novamente.",
            "request_id": str(uuid4()),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Return safe database errors instead of raw SQL details."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "database_error",
            "detail": "Serviço temporariamente indisponível. Tente novamente em alguns instantes.",
            "request_id": str(uuid4()),
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    """Return a generic message for unexpected errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "detail": "Erro interno ao processar a solicitação.",
            "request_id": str(uuid4()),
        },
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
    assigned_to: str | None = Query(None, description="Filtrar por técnico responsável"),
    origin: str | None = Query(None, description="Filtrar por origem do chamado"),
    search: str | None = Query(None, min_length=2, description="Buscar em título, descrição, nome ou email"),
    sort: str = Query("recent", pattern="^(recent|priority)$", description="Ordenar por recent ou priority"),
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
        assigned_to=assigned_to,
        origin=origin,
        search=search,
        sort=sort,
    )


@app.get("/tickets/export.csv", tags=["Tickets"])
def export_tickets_csv(service: TicketService = Depends(get_ticket_service)):
    """Exportar chamados para CSV compatível com Excel/LibreOffice."""
    tickets = service.list_tickets(page=1, page_size=100, sort="recent").tickets

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([
        "id",
        "titulo",
        "categoria",
        "prioridade",
        "status",
        "origem",
        "solicitante",
        "email",
        "tecnico",
        "feedback",
        "criado_em",
        "atualizado_em",
        "resolvido_em",
    ])

    for ticket in tickets:
        writer.writerow([
            ticket.id,
            ticket.title,
            ticket.category,
            ticket.priority,
            ticket.status,
            ticket.origin,
            ticket.requester_name,
            ticket.requester_email,
            ticket.assigned_to or "",
            ticket.feedback or "",
            ticket.created_at.isoformat() if ticket.created_at else "",
            ticket.updated_at.isoformat() if ticket.updated_at else "",
            ticket.resolved_at.isoformat() if ticket.resolved_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=ivan-helpdesk-chamados.csv"},
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
