from dataclasses import dataclass
from typing import Iterable, Optional

from models import Ticket


@dataclass(frozen=True)
class HelpdeskFilterOptions:
    origins: list[str]
    statuses: list[str]
    priorities: list[str]


def _enum_value(value: object) -> str:
    return getattr(value, "value", str(value))


def build_filter_options(tickets: Iterable[Ticket]) -> HelpdeskFilterOptions:
    rows = list(tickets)
    origins = sorted(
        {
            ticket.solicitante_setor.strip()
            for ticket in rows
            if ticket.solicitante_setor and ticket.solicitante_setor.strip()
        }
    )
    statuses = sorted({_enum_value(ticket.status) for ticket in rows})
    priorities = sorted({_enum_value(ticket.prioridade) for ticket in rows})

    return HelpdeskFilterOptions(origins=origins, statuses=statuses, priorities=priorities)


def filter_tickets_for_view(
    tickets: Iterable[Ticket],
    *,
    origin: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
) -> list[Ticket]:
    selected_origin = origin.strip() if origin else ""
    selected_status = status.strip() if status else ""
    selected_priority = priority.strip() if priority else ""

    filtered: list[Ticket] = []
    for ticket in tickets:
        ticket_origin = ticket.solicitante_setor or ""
        ticket_status = _enum_value(ticket.status)
        ticket_priority = _enum_value(ticket.prioridade)

        if selected_origin and ticket_origin != selected_origin:
            continue
        if selected_status and ticket_status != selected_status:
            continue
        if selected_priority and ticket_priority != selected_priority:
            continue

        filtered.append(ticket)

    return filtered
