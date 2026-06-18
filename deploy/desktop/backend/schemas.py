"""Pydantic schemas for Ivan Helpdesk API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class TicketBase(BaseModel):
    """Base ticket fields."""
    title: str = Field(..., min_length=3, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=10, description="Detailed description")
    category: str = Field(..., description="Category: hardware, software, network, access, other")
    priority: str = Field(default="media", description="Priority: baixa, media, alta, critica")
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
    status: Optional[str] = Field(default=None, description="Status: aberto, em_andamento, resolvido, fechado")
    assigned_to: Optional[str] = Field(default=None, max_length=100)
    resolution: Optional[str] = None
    feedback: Optional[int] = Field(default=None, ge=1, le=5, description="Nota de feedback de 1 a 5")


class TicketResponse(TicketBase):
    """Schema for ticket responses."""
    id: int
    status: str
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    feedback: Optional[int] = None

    class Config:
        from_attributes = True


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
    version: str = "0.3.0"
    database: str = "connected"