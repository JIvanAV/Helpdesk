from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Ticket, TicketStatus, TicketPriority
from schemas import TicketCreate, TicketUpdate


def create_ticket(db: Session, ticket: TicketCreate) -> Ticket:
    db_ticket = Ticket(
        titulo=ticket.titulo,
        descricao=ticket.descricao,
        categoria=ticket.categoria,
        prioridade=ticket.prioridade,
        solicitante_nome=ticket.solicitante_nome,
        solicitante_email=ticket.solicitante_email,
        solicitante_setor=ticket.solicitante_setor,
        status=TicketStatus.ABERTO,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_ticket(db: Session, ticket_id: int) -> Optional[Ticket]:
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[TicketStatus] = None,
    prioridade: Optional[TicketPriority] = None,
    tecnico_responsavel: Optional[str] = None,
) -> tuple[List[Ticket], int]:
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.status == status)
    if prioridade:
        query = query.filter(Ticket.prioridade == prioridade)
    if tecnico_responsavel:
        query = query.filter(Ticket.tecnico_responsavel == tecnico_responsavel)

    total = query.count()
    tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return tickets, total


def update_ticket(db: Session, ticket_id: int, ticket_update: TicketUpdate) -> Optional[Ticket]:
    db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not db_ticket:
        return None

    update_data = ticket_update.model_dump(exclude_unset=True)

    # Handle status change to RESOLVIDO/FECHADO
    if "status" in update_data and update_data["status"] in (TicketStatus.RESOLVIDO, TicketStatus.FECHADO):
        if not db_ticket.closed_at:
            db_ticket.closed_at = datetime.utcnow()

    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int) -> bool:
    db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not db_ticket:
        return False
    db.delete(db_ticket)
    db.commit()
    return True


def get_ticket_stats(db: Session) -> dict:
    total = db.query(Ticket).count()
    by_status = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    by_priority = db.query(Ticket.prioridade, func.count(Ticket.id)).group_by(Ticket.prioridade).all()
    return {
        "total": total,
        "by_status": {status.value: count for status, count in by_status},
        "by_priority": {prio.value: count for prio, count in by_priority},
    }