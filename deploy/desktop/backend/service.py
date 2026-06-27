"""Service layer for Ivan Helpdesk business logic."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, case

from models import Ticket
from schemas import TicketCreate, TicketUpdate, TicketListResponse


class TicketService:
    """Business logic for ticket operations."""

    VALID_CATEGORIES = {"hardware", "software", "network", "access", "other"}
    VALID_PRIORITIES = {"baixa", "media", "alta", "critica"}
    VALID_STATUSES = {"aberto", "em_andamento", "resolvido", "fechado"}
    VALID_ORIGINS = {"email", "telefone", "whatsapp", "portal", "presencial"}

    def __init__(self, db: Session):
        self.db = db

    def _validate_category(self, category: str) -> str:
        cat = category.lower().strip()
        if cat not in self.VALID_CATEGORIES:
            raise ValueError(f"Categoria inválida: {category}. Válidas: {', '.join(self.VALID_CATEGORIES)}")
        return cat

    def _validate_priority(self, priority: str) -> str:
        pri = priority.lower().strip()
        if pri not in self.VALID_PRIORITIES:
            raise ValueError(f"Prioridade inválida: {priority}. Válidas: {', '.join(self.VALID_PRIORITIES)}")
        return pri

    def _validate_status(self, status: str) -> str:
        st = status.lower().strip()
        if st not in self.VALID_STATUSES:
            raise ValueError(f"Status inválido: {status}. Válidos: {', '.join(self.VALID_STATUSES)}")
        return st

    def _validate_origin(self, origin: str) -> str:
        normalized = origin.lower().strip().replace("e-mail", "email")
        if normalized not in self.VALID_ORIGINS:
            raise ValueError(f"Origem inválida: {origin}. Válidas: {', '.join(self.VALID_ORIGINS)}")
        return normalized

    def create_ticket(self, ticket_data: TicketCreate) -> Ticket:
        """Create a new ticket."""
        ticket = Ticket(
            title=ticket_data.title.strip(),
            description=ticket_data.description.strip(),
            category=self._validate_category(ticket_data.category),
            priority=self._validate_priority(ticket_data.priority),
            origin=self._validate_origin(ticket_data.origin),
            status="aberto",
            requester_name=ticket_data.requester_name.strip(),
            requester_email=ticket_data.requester_email.lower().strip(),
            requester_department=ticket_data.requester_department.strip() if ticket_data.requester_department else None,
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by ID."""
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()

    def list_tickets(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        requester_email: Optional[str] = None,
        assigned_to: Optional[str] = None,
        origin: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "recent",
    ) -> TicketListResponse:
        """List tickets with filters, sorting and pagination."""
        query = self.db.query(Ticket)

        if status:
            query = query.filter(Ticket.status == self._validate_status(status))
        if category:
            query = query.filter(Ticket.category == self._validate_category(category))
        if priority:
            query = query.filter(Ticket.priority == self._validate_priority(priority))
        if requester_email:
            query = query.filter(Ticket.requester_email == requester_email.lower().strip())
        if assigned_to:
            assignee = assigned_to.strip().lower()
            query = query.filter(func.lower(Ticket.assigned_to) == assignee)
        if origin:
            query = query.filter(Ticket.origin == self._validate_origin(origin))
        if search:
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(Ticket.title).like(term),
                    func.lower(Ticket.description).like(term),
                    func.lower(Ticket.requester_name).like(term),
                    func.lower(Ticket.requester_email).like(term),
                )
            )

        total = query.count()

        if sort == "priority":
            priority_order = case(
                (Ticket.priority == "critica", 0),
                (Ticket.priority == "alta", 1),
                (Ticket.priority == "media", 2),
                (Ticket.priority == "baixa", 3),
                else_=4,
            )
            query = query.order_by(priority_order, desc(Ticket.created_at))
        elif sort == "recent":
            query = query.order_by(desc(Ticket.created_at))
        else:
            raise ValueError("Ordenação inválida. Use: recent ou priority")

        tickets = (
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return TicketListResponse(
            tickets=tickets,
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_ticket(self, ticket_id: int, ticket_update: TicketUpdate) -> Optional[Ticket]:
        """
        Atualiza campos de um chamado existente.

        Nota: A resolução é cumulativa. Se o usuário enviar uma nova,
        ela é anexada ao histórico anterior com uma separação visual.
        """
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        # Converte para dict ignorando campos que não foram enviados na requisição
        update_data = ticket_update.model_dump(exclude_unset=True)

        # Validação centralizada de campos de texto/status
        if "category" in update_data and update_data["category"]:
            update_data["category"] = self._validate_category(update_data["category"])
        if "priority" in update_data and update_data["priority"]:
            update_data["priority"] = self._validate_priority(update_data["priority"])
        if "origin" in update_data and update_data["origin"]:
            update_data["origin"] = self._validate_origin(update_data["origin"])
        if "status" in update_data and update_data["status"]:
            new_status = self._validate_status(update_data["status"])
            update_data["status"] = new_status

            # Marca tempo de resolução se finalizado
            if new_status == "resolvido" and ticket.status != "resolvido":
                update_data["resolved_at"] = datetime.utcnow()
            elif new_status != "resolvido" and ticket.status == "resolvido":
                update_data["resolved_at"] = None

        # Regra de negócio para feedback (apenas em chamados finalizados)
        if "feedback" in update_data and update_data["feedback"] is not None:
            current_status = update_data.get("status", ticket.status)
            if current_status not in ["resolvido", "fechado"]:
                 raise ValueError("Feedback só pode ser adicionado em chamados finalizados.")
            if not (1 <= update_data["feedback"] <= 5):
                 raise ValueError("Feedback deve ser entre 1 e 5.")

        # Lógica de histórico para o campo de resolução
        if "resolution" in update_data:
            if not update_data["resolution"]:
                update_data.pop("resolution")
            else:
                new_resolution = update_data["resolution"].strip()
                current_res = ticket.resolution or ""
                timestamp = datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
                technician = update_data.get("assigned_to") or ticket.assigned_to or "Técnico não informado"
                history_entry = f"[{timestamp}] {technician}\n{new_resolution}"

                # Se já existe, anexa ao histórico para não perder registros.
                # Isso transforma o campo em um log cumulativo de comentários técnicos.
                if current_res and new_resolution not in current_res:
                    update_data["resolution"] = f"{current_res}\n\n---\n{history_entry}"
                elif current_res:
                    update_data["resolution"] = current_res
                else:
                    update_data["resolution"] = history_entry

        # Aplica todas as mudanças validadas
        for field, value in update_data.items():
            setattr(ticket, field, value)

        ticket.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def delete_ticket(self, ticket_id: int) -> bool:
        """Delete a ticket (soft delete not implemented, hard delete)."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False
        self.db.delete(ticket)
        self.db.commit()
        return True

    def get_stats(self) -> dict:
        """Get ticket statistics for dashboard."""
        total = self.db.query(Ticket).count()
        by_status = dict(
            self.db.query(Ticket.status, func.count(Ticket.id))
            .group_by(Ticket.status)
            .all()
        )
        by_priority = dict(
            self.db.query(Ticket.priority, func.count(Ticket.id))
            .group_by(Ticket.priority)
            .all()
        )
        by_category = dict(
            self.db.query(Ticket.category, func.count(Ticket.id))
            .group_by(Ticket.category)
            .all()
        )
        by_origin = dict(
            self.db.query(Ticket.origin, func.count(Ticket.id))
            .group_by(Ticket.origin)
            .all()
        )
        open_count = self.db.query(Ticket).filter(Ticket.status == "aberto").count()

        return {
            "total": total,
            "open": open_count,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "by_origin": by_origin,
        }
