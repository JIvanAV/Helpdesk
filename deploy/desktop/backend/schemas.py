from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field
from models import TicketStatus, TicketPriority


class TicketBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    descricao: str = Field(..., min_length=1)
    categoria: Optional[str] = Field(None, max_length=100)
    prioridade: TicketPriority = TicketPriority.MEDIA
    solicitante_nome: str = Field(..., min_length=1, max_length=150)
    solicitante_email: EmailStr
    solicitante_setor: Optional[str] = Field(None, max_length=100)


class TicketCreate(TicketBase):
    pass


class PortfolioLeadIngestion(BaseModel):
    requestId: str = Field(..., min_length=8, max_length=80)
    nome: str = Field(..., min_length=2, max_length=150)
    telefone: str = Field(..., min_length=8, max_length=32)
    email: Optional[EmailStr] = None
    origem: Literal["portfolio", "whatsapp", "helpdesk", "automacao"]
    servicoInteresse: str = Field(..., min_length=3, max_length=160)
    mensagemOriginal: str = Field(..., min_length=10, max_length=1600)
    status: Literal["novo", "em_contato", "agendado", "concluido", "perdido"] = "novo"
    linkOrigem: str = Field(..., min_length=8, max_length=300)
    criadoEm: datetime
    proximoPasso: str = Field(..., min_length=5, max_length=240)
    confirmedByHuman: bool = False


class TicketUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    descricao: Optional[str] = Field(None, min_length=1)
    status: Optional[TicketStatus] = None
    prioridade: Optional[TicketPriority] = None
    categoria: Optional[str] = Field(None, max_length=100)
    tecnico_responsavel: Optional[str] = Field(None, max_length=150)
    solicitante_setor: Optional[str] = Field(None, max_length=100)


class TicketResponse(TicketBase):
    id: int
    status: TicketStatus
    tecnico_responsavel: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
    page: int
    size: int


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"