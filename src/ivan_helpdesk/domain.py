from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from itertools import count
from typing import Iterable


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class Ticket:
    id: int
    title: str
    description: str
    requester: str
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class HelpdeskService:
    """In-memory helpdesk service used by the first MVP iteration."""

    def __init__(self) -> None:
        self._ids = count(1)
        self._tickets: dict[int, Ticket] = {}

    def create_ticket(
        self,
        *,
        title: str,
        description: str,
        requester: str,
        priority: TicketPriority | str = TicketPriority.MEDIUM,
    ) -> Ticket:
        title = title.strip()
        description = description.strip()
        requester = requester.strip()
        if not title:
            raise ValueError("title is required")
        if not description:
            raise ValueError("description is required")
        if not requester:
            raise ValueError("requester is required")

        ticket = Ticket(
            id=next(self._ids),
            title=title,
            description=description,
            requester=requester,
            priority=TicketPriority(priority),
        )
        self._tickets[ticket.id] = ticket
        return ticket

    def list_tickets(
        self,
        *,
        status: TicketStatus | str | None = None,
        priority: TicketPriority | str | None = None,
    ) -> list[Ticket]:
        tickets: Iterable[Ticket] = self._tickets.values()
        if status is not None:
            wanted_status = TicketStatus(status)
            tickets = (ticket for ticket in tickets if ticket.status == wanted_status)
        if priority is not None:
            wanted_priority = TicketPriority(priority)
            tickets = (ticket for ticket in tickets if ticket.priority == wanted_priority)
        return sorted(tickets, key=lambda ticket: ticket.id)

    def get_ticket(self, ticket_id: int) -> Ticket:
        try:
            return self._tickets[ticket_id]
        except KeyError as exc:
            raise KeyError(f"ticket {ticket_id} not found") from exc

    def update_status(self, ticket_id: int, status: TicketStatus | str) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        new_status = TicketStatus(status)
        if ticket.status == TicketStatus.CLOSED and new_status != TicketStatus.CLOSED:
            raise ValueError("closed tickets cannot be reopened in MVP")
        ticket.status = new_status
        ticket.updated_at = datetime.now(timezone.utc)
        return ticket

    def summary(self) -> dict[str, int]:
        return {status.value: len(self.list_tickets(status=status)) for status in TicketStatus}
