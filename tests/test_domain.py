import pytest

from ivan_helpdesk import HelpdeskService, TicketPriority, TicketStatus


def test_create_ticket_with_required_fields():
    service = HelpdeskService()

    ticket = service.create_ticket(
        title="Computador sem rede",
        description="Usuário não consegue acessar sistemas internos.",
        requester="José Ivan",
        priority=TicketPriority.HIGH,
    )

    assert ticket.id == 1
    assert ticket.status == TicketStatus.OPEN
    assert ticket.priority == TicketPriority.HIGH


def test_create_ticket_validates_empty_fields():
    service = HelpdeskService()

    with pytest.raises(ValueError, match="title is required"):
        service.create_ticket(title=" ", description="desc", requester="user")


def test_list_tickets_can_filter_by_status_and_priority():
    service = HelpdeskService()
    first = service.create_ticket(title="A", description="desc", requester="u", priority="high")
    service.create_ticket(title="B", description="desc", requester="u", priority="low")

    service.update_status(first.id, TicketStatus.IN_PROGRESS)

    assert service.list_tickets(status="in_progress") == [first]
    assert service.list_tickets(priority="high") == [first]


def test_closed_ticket_cannot_be_reopened_in_mvp():
    service = HelpdeskService()
    ticket = service.create_ticket(title="A", description="desc", requester="u")
    service.update_status(ticket.id, TicketStatus.CLOSED)

    with pytest.raises(ValueError, match="closed tickets cannot be reopened"):
        service.update_status(ticket.id, TicketStatus.OPEN)


def test_summary_counts_tickets_by_status():
    service = HelpdeskService()
    first = service.create_ticket(title="A", description="desc", requester="u")
    service.create_ticket(title="B", description="desc", requester="u")
    service.update_status(first.id, TicketStatus.RESOLVED)

    assert service.summary() == {
        "open": 1,
        "in_progress": 0,
        "resolved": 1,
        "closed": 0,
    }
