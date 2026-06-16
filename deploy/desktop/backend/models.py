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
    resolution = Column(Text, nullable=True)
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

    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title}', status='{self.status}', priority='{self.priority}')>"