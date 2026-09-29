import unittest

from models import Ticket, TicketPriority, TicketStatus
from triage import build_triage_summary, needs_follow_up


def make_ticket(title, status, priority, origin="helpdesk", description="Caso comum"):
    ticket = Ticket(
        titulo=title,
        descricao=description,
        status=status,
        prioridade=priority,
        solicitante_nome="José Ivan",
        solicitante_email="jose@example.com",
        solicitante_setor=origin,
    )
    return ticket


class TriageSummaryTest(unittest.TestCase):
    def test_counts_open_attention_portfolio_and_follow_up_cases(self):
        tickets = [
            make_ticket(
                "Lead do portfólio",
                TicketStatus.ABERTO,
                TicketPriority.ALTA,
                origin="portfolio",
                description="Próximo passo: responder pelo WhatsApp.",
            ),
            make_ticket("Chamado resolvido", TicketStatus.RESOLVIDO, TicketPriority.CRITICA),
            make_ticket("Aguardando retorno", TicketStatus.AGUARDANDO_USUARIO, TicketPriority.MEDIA),
        ]

        summary = build_triage_summary(tickets)

        self.assertEqual(summary.total_cases, 3)
        self.assertEqual(summary.open_cases, 2)
        self.assertEqual(summary.attention_cases, 1)
        self.assertEqual(summary.portfolio_leads, 1)
        self.assertEqual(summary.waiting_follow_up, 2)
        self.assertTrue(summary.has_work)

    def test_closed_case_with_follow_up_text_does_not_count_as_pending_work(self):
        ticket = make_ticket(
            "Caso encerrado",
            TicketStatus.FECHADO,
            TicketPriority.ALTA,
            description="Próximo passo já concluído.",
        )

        summary = build_triage_summary([ticket])

        self.assertEqual(summary.open_cases, 0)
        self.assertEqual(summary.waiting_follow_up, 0)
        self.assertFalse(summary.has_work)
        self.assertTrue(needs_follow_up(ticket))


if __name__ == "__main__":
    unittest.main()
