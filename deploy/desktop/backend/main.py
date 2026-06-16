from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
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