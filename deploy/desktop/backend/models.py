"""SQLAlchemy ORM models for Ivan Helpdesk."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func

from database import Base


class Ticket(Base):
    """Ticket ORM model."""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # hardware, software, network, access, other
    priority = Column(String(20), nullable=False, default="media", index=True)  # baixa, media, alta, critica
    status = Column(String(20), nullable=False, default="aberto", index=True)  # aberto, em_andamento, resolvido, fechado

    # Requester info
    requester_name = Column(String(100), nullable=False)
    requester_email = Column(String(255), nullable=False, index=True)
    requester_department = Column(String(100), nullable=True)

    # Assignment & resolution
    assigned_to = Column(String(100), nullable=True, index=True)
    origin = Column(String(50), nullable=False, default="portal", index=True)  # email, telefone, whatsapp, portal, presencial
    resolution = Column(Text, nullable=True)
    internal_comments = Column(Text, nullable=True)
    feedback = Column(Integer, nullable=True)  # 1-5 feedback score

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_category_status", "category", "status"),
        Index("ix_tickets_requester_email_created", "requester_email", "created_at"),
    )

    @property
    def sla_status(self) -> str:
        """Classify open ticket SLA from its age for the API/frontend."""
        if self.status in {"resolvido", "fechado"}:
            return "finalizado"

        created_at = self.created_at
        if not created_at:
            return "no_prazo"

        age_hours = (datetime.utcnow() - created_at.replace(tzinfo=None)).total_seconds() / 3600
        if age_hours > 48:
            return "atrasado"
        if age_hours > 24:
            return "atencao"
        return "no_prazo"

    @property
    def timeline(self) -> list[dict[str, str]]:
        """Build a simple audit-style timeline from the ticket's current fields."""
        events = [
            {
                "label": "Chamado criado",
                "description": f"Solicitante: {self.requester_name}",
                "occurred_at": self.created_at.isoformat() if self.created_at else "",
            }
        ]

        if self.assigned_to:
            events.append(
                {
                    "label": "Técnico atribuído",
                    "description": f"Responsável: {self.assigned_to}",
                    "occurred_at": self.updated_at.isoformat() if self.updated_at else "",
                }
            )

        if self.updated_at and self.created_at and self.updated_at != self.created_at:
            events.append(
                {
                    "label": "Chamado atualizado",
                    "description": f"Status atual: {self.status}",
                    "occurred_at": self.updated_at.isoformat(),
                }
            )

        if self.resolved_at:
            events.append(
                {
                    "label": "Chamado resolvido",
                    "description": "Atendimento finalizado com resolução registrada.",
                    "occurred_at": self.resolved_at.isoformat(),
                }
            )

        return events

    @property
    def internal_comment_count(self) -> int:
        """Count appended internal technician comments."""
        if not self.internal_comments:
            return 0
        return self.internal_comments.count("[comentário interno]")

    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title}', status='{self.status}', priority='{self.priority}')>"