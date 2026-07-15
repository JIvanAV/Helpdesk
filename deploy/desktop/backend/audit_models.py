from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class TicketAuditEvent(Base):
    """Audit trail for ticket changes."""
    __tablename__ = "ticket_audit_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # status_change, assignment, resolution, note_added
    description = Column(Text, nullable=False)
    technician = Column(String(100), nullable=True)  # Name of tech who made the change
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("Ticket", backref="audit_events")
