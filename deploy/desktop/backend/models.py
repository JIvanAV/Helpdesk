from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from database import Base


class TicketStatus(str, enum.Enum):
    ABERTO = "ABERTO"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    AGUARDANDO_USUARIO = "AGUARDANDO_USUARIO"
    RESOLVIDO = "RESOLVIDO"
    FECHADO = "FECHADO"


class TicketPriority(str, enum.Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=False)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.ABERTO, nullable=False)
    prioridade = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIA, nullable=False)
    categoria = Column(String(100), nullable=True)
    solicitante_nome = Column(String(150), nullable=False)
    solicitante_email = Column(String(150), nullable=False)
    solicitante_setor = Column(String(100), nullable=True)
    tecnico_responsavel = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Ticket(id={self.id}, titulo='{self.titulo}', status='{self.status.value}')>"