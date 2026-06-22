from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from enum import Enum
from itertools import count
from typing import Iterable


MAX_TITLE_LEN = 100
MAX_DESCRIPTION_LEN = 2000
MAX_REQUESTER_LEN = 100
REDACTION = "[REDACTED]"
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)\b(password|passwd|senha|token|secret|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
)


def _redact_sensitive_values(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}={REDACTION}" if match.lastindex else REDACTION, redacted)
    return redacted


def _clean_field(value: str, *, field: str, max_length: int) -> str:
    cleaned = _redact_sensitive_values(value.strip())
    if not cleaned:
        raise ValueError(f"{field} is required")
    if len(cleaned) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters")
    return cleaned


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
    resolution: str | None = None
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
        title = _clean_field(title, field="title", max_length=MAX_TITLE_LEN)
        description = _clean_field(
            description,
            field="description",
            max_length=MAX_DESCRIPTION_LEN,
        )
        requester = _clean_field(requester, field="requester", max_length=MAX_REQUESTER_LEN)

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

    def update_status(self, ticket_id: int, status: TicketStatus | str, resolution: str | None = None) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        new_status = TicketStatus(status)
        if ticket.status == TicketStatus.CLOSED and new_status != TicketStatus.CLOSED:
            raise ValueError("closed tickets cannot be reopened in MVP")
        ticket.status = new_status
        if resolution:
            cleaned_resolution = _clean_field(
                resolution,
                field="resolution",
                max_length=MAX_DESCRIPTION_LEN,
            )
            ticket.resolution = (
                f"{ticket.resolution}\n\n---\n{cleaned_resolution}"
                if ticket.resolution
                else cleaned_resolution
            )
        ticket.updated_at = datetime.now(timezone.utc)
        return ticket

    def summary(self) -> dict[str, int]:
        return {status.value: len(self.list_tickets(status=status)) for status in TicketStatus}
