import html

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from database import get_db, init_db
from models import Ticket, TicketStatus, TicketPriority
from schemas import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketListResponse,
    HealthResponse,
)
from service import (
    create_ticket,
    get_ticket,
    get_tickets,
    update_ticket,
    delete_ticket,
    get_ticket_stats,
)

app = FastAPI(
    title="Helpdesk API",
    description="Sistema de Helpdesk / Service Desk para gerenciamento de chamados",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/", response_class=HTMLResponse, tags=["Visualização"])
def view_cases_endpoint(db: Session = Depends(get_db)):
    tickets, total = get_tickets(db, skip=0, limit=100)
    cards = []
    for ticket in tickets:
        cards.append(
            f"""
            <article class="card priority-{html.escape(ticket.prioridade.value.lower())}">
                <div class="meta">
                    <span>{html.escape(ticket.solicitante_setor or 'Plataforma')}</span>
                    <span>{html.escape(ticket.prioridade.value)}</span>
                    <span>{html.escape(ticket.status.value)}</span>
                </div>
                <h2>#{ticket.id} {html.escape(ticket.titulo)}</h2>
                <p>{html.escape(ticket.descricao).replace(chr(10), '<br>')}</p>
            </article>
            """
        )
    return """
    <!doctype html>
    <html lang="pt-BR">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Ivan Helpdesk - Casos de candidaturas</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; background: #0f172a; color: #e5e7eb; }
            header { padding: 22px 16px; background: #111827; border-bottom: 1px solid #334155; }
            main { padding: 16px; display: grid; gap: 14px; max-width: 980px; margin: 0 auto; }
            h1 { margin: 0 0 8px; font-size: 1.45rem; }
            h2 { margin: 10px 0; font-size: 1.05rem; }
            p { line-height: 1.45; font-size: .94rem; }
            .summary { color: #cbd5e1; margin: 0; }
            .card { background: #1e293b; border: 1px solid #334155; border-left: 6px solid #38bdf8; border-radius: 14px; padding: 14px; box-shadow: 0 8px 24px #02061755; }
            .priority-critica { border-left-color: #f97316; }
            .priority-alta { border-left-color: #22c55e; }
            .meta { display: flex; gap: 8px; flex-wrap: wrap; }
            .meta span { background: #0f172a; color: #bae6fd; border: 1px solid #334155; border-radius: 999px; padding: 4px 9px; font-size: .78rem; }
            a { color: #7dd3fc; }
        </style>
    </head>
    <body>
        <header>
            <h1>Ivan Helpdesk - Casos baseados nas vagas selecionadas</h1>
            <p class="summary">Total de casos: """ + str(total) + """. Status externo: confirmação/protocolo ainda pendente.</p>
        </header>
        <main>""" + "\n".join(cards) + """</main>
    </body>
    </html>
    """


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(status="ok")


@app.post("/tickets", response_model=TicketResponse, status_code=201, tags=["Tickets"])
def create_ticket_endpoint(ticket: TicketCreate, db: Session = Depends(get_db)):
    db_ticket = create_ticket(db, ticket)
    return db_ticket


@app.get("/tickets", response_model=TicketListResponse, tags=["Tickets"])
def list_tickets_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TicketStatus] = None,
    prioridade: Optional[TicketPriority] = None,
    tecnico_responsavel: Optional[str] = None,
    db: Session = Depends(get_db),
):
    tickets, total = get_tickets(db, skip, limit, status, prioridade, tecnico_responsavel)
    return TicketListResponse(tickets=tickets, total=total, page=skip // limit + 1, size=limit)


@app.get("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def get_ticket_endpoint(ticket_id: int, db: Session = Depends(get_db)):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return db_ticket


@app.put("/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def update_ticket_endpoint(ticket_id: int, ticket_update: TicketUpdate, db: Session = Depends(get_db)):
    db_ticket = update_ticket(db, ticket_id, ticket_update)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return db_ticket


@app.delete("/tickets/{ticket_id}", status_code=204, tags=["Tickets"])
def delete_ticket_endpoint(ticket_id: int, db: Session = Depends(get_db)):
    success = delete_ticket(db, ticket_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    return None


@app.get("/tickets/stats/summary", tags=["Stats"])
def get_stats_endpoint(db: Session = Depends(get_db)):
    return get_ticket_stats(db)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)