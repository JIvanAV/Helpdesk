from dataclasses import dataclass
from typing import Iterable

from models import Ticket, TicketPriority, TicketStatus


OPEN_STATUSES = {
    TicketStatus.ABERTO,
    TicketStatus.EM_ANDAMENTO,
    TicketStatus.AGUARDANDO_USUARIO,
}
ATTENTION_PRIORITIES = {TicketPriority.ALTA, TicketPriority.CRITICA}
FOLLOW_UP_MARKERS = ("próximo passo", "proximo passo", "aguardando", "retornar", "responder")


@dataclass(frozen=True)
class TriageSummary:
    total_cases: int
    open_cases: int
    attention_cases: int
    portfolio_leads: int
    waiting_follow_up: int

    @property
    def has_work(self) -> bool:
        return self.open_cases > 0 or self.waiting_follow_up > 0


def build_triage_summary(tickets: Iterable[Ticket]) -> TriageSummary:
    rows = list(tickets)
    open_cases = [ticket for ticket in rows if ticket.status in OPEN_STATUSES]

    attention_cases = sum(
        1 for ticket in open_cases if ticket.prioridade in ATTENTION_PRIORITIES
    )
    portfolio_leads = sum(
        1 for ticket in rows if (ticket.solicitante_setor or "").lower() == "portfolio"
    )
    waiting_follow_up = sum(1 for ticket in open_cases if needs_follow_up(ticket))

    return TriageSummary(
        total_cases=len(rows),
        open_cases=len(open_cases),
        attention_cases=attention_cases,
        portfolio_leads=portfolio_leads,
        waiting_follow_up=waiting_follow_up,
    )


def needs_follow_up(ticket: Ticket) -> bool:
    text = f"{ticket.titulo}\n{ticket.descricao}".lower()
    return any(marker in text for marker in FOLLOW_UP_MARKERS)
