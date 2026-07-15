"""Service layer for Ivan Helpdesk business logic."""

from datetime import datetime, time
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_, case

from models import Ticket
from schemas import TicketCreate, TicketUpdate, TicketCommentCreate, TicketListResponse


class TicketService:
    """Business logic for ticket operations."""

    VALID_CATEGORIES = {"hardware", "software", "network", "access", "other"}
    VALID_PRIORITIES = {"baixa", "media", "alta", "critica"}
    VALID_STATUSES = {"aberto", "em_andamento", "resolvido", "fechado"}
    VALID_ORIGINS = {"email", "telefone", "whatsapp", "portal", "presencial"}

    def __init__(self, db: Session):
        self.db = db

    def _normalize_choice(self, field_name: str, value: str, valid_values: set[str]) -> str:
        """Normalize and validate one controlled-vocabulary field."""
        normalized = value.lower().strip().replace("e-mail", "email")
        if normalized not in valid_values:
            allowed = ", ".join(sorted(valid_values))
            raise ValueError(f"{field_name} inválida: {value}. Válidas: {allowed}")
        return normalized

    def _validate_category(self, category: str) -> str:
        return self._normalize_choice("Categoria", category, self.VALID_CATEGORIES)

    def _validate_priority(self, priority: str) -> str:
        return self._normalize_choice("Prioridade", priority, self.VALID_PRIORITIES)

    def _validate_status(self, status: str) -> str:
        return self._normalize_choice("Status", status, self.VALID_STATUSES)

    def _validate_origin(self, origin: str) -> str:
        return self._normalize_choice("Origem", origin, self.VALID_ORIGINS)

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

    @staticmethod
    def _human_timestamp() -> str:
        """Format timestamps used in notes shown to the support team."""
        return datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")

    @staticmethod
    def _technician_name(*candidates: Optional[str]) -> str:
        """Return the first filled technician name, or a safe fallback."""
        for name in candidates:
            if name and name.strip():
                return name.strip()
        return "Técnico não informado"

    def _append_internal_comment(self, ticket: Ticket, comment: str, technician: Optional[str] = None) -> None:
        """Append an internal technician comment without overwriting prior notes."""
        clean_comment = comment.strip()
        if not clean_comment:
            return

        author = self._technician_name(technician, ticket.assigned_to)
        entry = f"[{self._human_timestamp()}] [comentário interno] {author}\n{clean_comment}"
        ticket.internal_comments = f"{ticket.internal_comments}\n\n---\n{entry}" if ticket.internal_comments else entry

    def add_internal_comment(self, ticket_id: int, comment_data: TicketCommentCreate) -> Optional[Ticket]:
        """Add one internal technician comment to an existing ticket."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        self._append_internal_comment(ticket, comment_data.comment, comment_data.technician)
        ticket.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

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
        if "internal_comment" in update_data:
            comment = update_data.pop("internal_comment")
            if comment:
                self._append_internal_comment(
                    ticket,
                    comment,
                    update_data.get("assigned_to") or ticket.assigned_to,
                )

        if "resolution" in update_data:
            if not update_data["resolution"]:
                update_data.pop("resolution")
            else:
                new_resolution = update_data["resolution"].strip()
                current_res = ticket.resolution or ""
                technician = self._technician_name(update_data.get("assigned_to"), ticket.assigned_to)
                history_entry = f"[{self._human_timestamp()}] {technician}\n{new_resolution}"

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
        by_sla_status = {
            "no_prazo": 0,
            "atencao": 0,
            "atrasado": 0,
            "finalizado": 0,
        }
        for ticket in self.db.query(Ticket).all():
            by_sla_status[ticket.sla_status] = by_sla_status.get(ticket.sla_status, 0) + 1
        open_count = self.db.query(Ticket).filter(Ticket.status == "aberto").count()

        today_start = datetime.combine(datetime.utcnow().date(), time.min)
        today_created = self.db.query(Ticket).filter(Ticket.created_at >= today_start).count()
        today_resolved = self.db.query(Ticket).filter(Ticket.resolved_at >= today_start).count()

        # Média de tempo para resolução (em horas)
        # Filtra tickets resolvidos, calcula diferença entre resolved_at e created_at
        avg_res_time = (
            self.db.query(func.avg(func.julianday(Ticket.resolved_at) - func.julianday(Ticket.created_at)))
            .filter(Ticket.resolved_at.isnot(None))
            .scalar()
        )
        avg_res_hours = round(avg_res_time * 24, 2) if avg_res_time else 0.0

        return {
            "total": total,
            "open": open_count,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "by_origin": by_origin,
            "by_sla_status": by_sla_status,
            "avg_resolution_hours": avg_res_hours,
            "today": {
                "created": today_created,
                "resolved": today_resolved,
            },
        }
