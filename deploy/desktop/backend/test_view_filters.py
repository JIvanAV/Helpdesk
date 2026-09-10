import unittest
from datetime import datetime

from models import Ticket, TicketPriority, TicketStatus
from view_filters import build_filter_options, filter_tickets_for_view


class HelpdeskViewFiltersTest(unittest.TestCase):
    def make_ticket(self, **overrides):
        data = {
            "id": 1,
            "titulo": "Lead do portfólio",
            "descricao": "Cliente pediu suporte remoto",
            "status": TicketStatus.ABERTO,
            "prioridade": TicketPriority.ALTA,
            "categoria": "Lead Portfolio",
            "solicitante_nome": "Maria Silva",
            "solicitante_email": "maria@example.com",
            "solicitante_setor": "portfolio",
            "created_at": datetime(2026, 9, 10, 10, 0),
            "updated_at": datetime(2026, 9, 10, 10, 0),
        }
        data.update(overrides)
        return Ticket(**data)

    def test_filters_tickets_by_origin_status_and_priority(self):
        tickets = [
            self.make_ticket(id=1, solicitante_setor="portfolio", status=TicketStatus.ABERTO, prioridade=TicketPriority.ALTA),
            self.make_ticket(id=2, solicitante_setor="automacao", status=TicketStatus.ABERTO, prioridade=TicketPriority.MEDIA),
            self.make_ticket(id=3, solicitante_setor="portfolio", status=TicketStatus.FECHADO, prioridade=TicketPriority.ALTA),
        ]

        filtered = filter_tickets_for_view(
            tickets,
            origin="portfolio",
            status="ABERTO",
            priority="ALTA",
        )

        self.assertEqual([ticket.id for ticket in filtered], [1])

    def test_builds_human_filter_options_from_existing_tickets(self):
        tickets = [
            self.make_ticket(id=1, solicitante_setor="portfolio", status=TicketStatus.ABERTO, prioridade=TicketPriority.ALTA),
            self.make_ticket(id=2, solicitante_setor="automacao", status=TicketStatus.EM_ANDAMENTO, prioridade=TicketPriority.MEDIA),
            self.make_ticket(id=3, solicitante_setor=None, status=TicketStatus.ABERTO, prioridade=TicketPriority.BAIXA),
        ]

        options = build_filter_options(tickets)

        self.assertEqual(options.origins, ["automacao", "portfolio"])
        self.assertIn("ABERTO", options.statuses)
        self.assertIn("EM_ANDAMENTO", options.statuses)
        self.assertIn("ALTA", options.priorities)
        self.assertIn("MEDIA", options.priorities)


if __name__ == "__main__":
    unittest.main()
