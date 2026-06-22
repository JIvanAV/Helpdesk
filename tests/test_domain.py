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


def test_create_ticket_redacts_sensitive_values_from_user_input():
    service = HelpdeskService()

    fake_token = "ghp_1234567890abcdefghij1234567890abcdefghij"
    ticket = service.create_ticket(
        title="VPN password=SuperSecret123 falhando",
        description=f"Token: {fake_token}",
        requester="José Ivan",
    )

    assert "SuperSecret123" not in ticket.title
    assert fake_token not in ticket.description
    assert "[REDACTED]" in ticket.title
    assert "[REDACTED]" in ticket.description


def test_create_ticket_limits_user_controlled_field_sizes():
    service = HelpdeskService()

    with pytest.raises(ValueError, match="title must be at most 100 characters"):
        service.create_ticket(title="A" * 101, description="desc", requester="user")

    with pytest.raises(ValueError, match="description must be at most 2000 characters"):
        service.create_ticket(title="A", description="D" * 2001, requester="user")


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


def test_update_status_appends_resolution_history():
    service = HelpdeskService()
    ticket = service.create_ticket(title="A", description="desc", requester="u")

    service.update_status(ticket.id, TicketStatus.IN_PROGRESS, resolution="Primeira triagem realizada")
    updated = service.update_status(ticket.id, TicketStatus.RESOLVED, resolution="Correção validada com usuário")

    assert "Primeira triagem realizada" in updated.resolution
    assert "Correção validada com usuário" in updated.resolution
    assert updated.resolution.index("Primeira triagem realizada") < updated.resolution.index("Correção validada com usuário")


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
