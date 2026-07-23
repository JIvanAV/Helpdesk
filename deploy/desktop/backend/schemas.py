"""Pydantic schemas for Ivan Helpdesk API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


API_VERSION = "0.4.0"


class TicketBase(BaseModel):
    """Base ticket fields."""
    title: str = Field(..., min_length=3, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=10, description="Detailed description")
    category: str = Field(..., description="Category: hardware, software, network, access, other")
    priority: str = Field(default="media", description="Priority: baixa, media, alta, critica")
    impact: str = Field(default="baixo", description="Impacto operacional: baixo, medio, alto, parada_total")
    support_level: str = Field(default="N1", description="Nível de suporte: N1 ou N2")
    origin: str = Field(default="portal", description="Origem: email, telefone, whatsapp, portal, presencial")
    requester_name: str = Field(..., min_length=2, max_length=100)
    requester_email: EmailStr
    requester_department: Optional[str] = Field(default=None, max_length=100)


class TicketCreate(TicketBase):
    """Schema for creating a new ticket."""
    pass


class TicketUpdate(BaseModel):
    """Schema for updating a ticket (partial)."""
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=10)
    category: Optional[str] = None
    priority: Optional[str] = None
    impact: Optional[str] = None
    support_level: Optional[str] = None
    status: Optional[str] = Field(default=None, description="Status: aberto, em_andamento, resolvido, fechado")
    assigned_to: Optional[str] = Field(default=None, max_length=100)
    origin: Optional[str] = None
    resolution: Optional[str] = None
    checklist_solution_registered: Optional[bool] = None
    checklist_user_validated: Optional[bool] = None
    checklist_evidence_collected: Optional[bool] = None
    checklist_equipment_ok: Optional[bool] = None
    internal_comment: Optional[str] = Field(default=None, max_length=1000)
    feedback: Optional[int] = Field(default=None, ge=1, le=5, description="Nota de feedback de 1 a 5")


class TicketCommentCreate(BaseModel):
    """Schema for adding an internal technician comment."""
    comment: str = Field(..., min_length=3, max_length=1000)
    technician: Optional[str] = Field(default=None, max_length=100)


class TicketTimelineEvent(BaseModel):
    """Computed event shown in the ticket timeline."""
    label: str
    description: str
    occurred_at: str


class TicketResponse(TicketBase):
    """Schema for ticket responses."""
    id: int
    status: str
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    checklist_solution_registered: bool = False
    checklist_user_validated: bool = False
    checklist_evidence_collected: bool = False
    checklist_equipment_ok: bool = False
    internal_comments: Optional[str] = None
    internal_comment_count: int = 0
    sla_status: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    feedback: Optional[int] = None
    timeline: list[TicketTimelineEvent] = Field(default_factory=list)

    # Pydantic v2: permite criar a resposta direto de objetos ORM do SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)


class TicketAuditEventResponse(BaseModel):
    """Audit event returned for one ticket."""
    id: int
    ticket_id: int
    event_type: str
    description: str
    technician: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketListResponse(BaseModel):
    """Paginated ticket list response."""
    tickets: list[TicketResponse]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "ivan-helpdesk"
    version: str = API_VERSION
    database: str = "connected"
