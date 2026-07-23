"""SQLAlchemy ORM models for Ivan Helpdesk."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base
from audit_models import TicketAuditEvent


class Ticket(Base):
    """Ticket ORM model."""

    CLOSED_STATUSES = {"resolvido", "fechado"}

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # hardware, software, network, access, other
    priority = Column(String(20), nullable=False, default="media", index=True)  # baixa, media, alta, critica
    impact = Column(String(20), nullable=False, default="baixo", index=True)  # baixo, medio, alto, parada_total
    status = Column(String(20), nullable=False, default="aberto", index=True)  # aberto, em_andamento, resolvido, fechado

    # Nível de suporte: N1 ou N2
    support_level = Column(String(2), nullable=False, default="N1", index=True)

    # Requester info
    requester_name = Column(String(100), nullable=False)
    requester_email = Column(String(255), nullable=False, index=True)
    requester_department = Column(String(100), nullable=True)

    # Assignment & resolution
    assigned_to = Column(String(100), nullable=True, index=True)
    origin = Column(String(50), nullable=False, default="portal", index=True)  # email, telefone, whatsapp, portal, presencial
    resolution = Column(Text, nullable=True)

    # Closure checklist
    checklist_solution_registered = Column(Integer, default=0)  # 0: false, 1: true
    checklist_user_validated = Column(Integer, default=0)
    checklist_evidence_collected = Column(Integer, default=0)
    checklist_equipment_ok = Column(Integer, default=0)

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
        Index("ix_tickets_status_support_level", "status", "support_level"),
    )

    @property
    def sla_status(self) -> str:
        """Classify open ticket SLA from its age for the API/frontend."""
        if self.status in self.CLOSED_STATUSES:
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

    def _timeline_event(self, label: str, description: str, occurred_at: Optional[datetime]) -> dict[str, str]:
        """Create one frontend-friendly timeline event."""
        return {
            "label": label,
            "description": description,
            "occurred_at": occurred_at.isoformat() if occurred_at else "",
        }

    @property
    def timeline(self) -> list[dict[str, str]]:
        """Build a simple audit-style timeline from the ticket's current fields."""
        events = [
            self._timeline_event(
                "Chamado criado",
                f"Solicitante: {self.requester_name}",
                self.created_at,
            )
        ]

        if self.assigned_to:
            events.append(
                self._timeline_event(
                    "Técnico atribuído",
                    f"Responsável: {self.assigned_to}",
                    self.updated_at,
                )
            )

        if self.support_level == "N2":
            events.append(
                self._timeline_event(
                    "Escalamento N2",
                    "Chamado movido para suporte especializado.",
                    self.updated_at,
                )
            )

        if self.updated_at and self.created_at and self.updated_at != self.created_at:
            events.append(
                self._timeline_event(
                    "Chamado atualizado",
                    f"Status atual: {self.status}",
                    self.updated_at,
                )
            )

        if self.resolved_at:
            events.append(
                self._timeline_event(
                    "Chamado resolvido",
                    "Atendimento finalizado com resolução registrada.",
                    self.resolved_at,
                )
            )

        return events

    @property
    def internal_comment_count(self) -> int:
        """Count appended internal technician comments."""
        if not self.internal_comments:
            return 0
        return self.internal_comments.count("[comentário interno]")

    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title}', status='{self.status}', priority='{self.priority}', level='{self.support_level}')>"
