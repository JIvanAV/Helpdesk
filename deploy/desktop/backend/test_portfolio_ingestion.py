import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import TicketPriority
from schemas import PortfolioLeadIngestion
from service import build_ticket_from_portfolio_lead, create_ticket_from_portfolio_lead


class PortfolioLeadIngestionTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def make_lead(self, **overrides):
        data = {
            "requestId": "8a4f2f44-2c51-4f6f-9a1d-8bdf4f1e6d22",
            "nome": "Maria Silva",
            "telefone": "(83) 99999-1111",
            "email": "maria@example.com",
            "origem": "portfolio",
            "servicoInteresse": "Suporte remoto para computador lento",
            "mensagemOriginal": "Preciso de ajuda para revisar um notebook usado no trabalho.",
            "status": "novo",
            "linkOrigem": "https://jose-ivan-ti-portfolio.vercel.app/#duvida-rapida",
            "criadoEm": datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc),
            "proximoPasso": "Responder pelo WhatsApp e confirmar o melhor horário.",
        }
        data.update(overrides)
        return PortfolioLeadIngestion(**data)

    def test_builds_human_readable_helpdesk_ticket(self):
        ticket = build_ticket_from_portfolio_lead(self.make_lead())

        self.assertEqual(ticket.titulo, "Lead do portfólio: Suporte remoto para computador lento")
        self.assertEqual(ticket.prioridade, TicketPriority.ALTA)
        self.assertEqual(ticket.solicitante_setor, "portfolio")
        self.assertIn("Request ID: 8a4f2f44-2c51-4f6f-9a1d-8bdf4f1e6d22", ticket.descricao)
        self.assertIn("Próximo passo: Responder pelo WhatsApp", ticket.descricao)

    def test_reuses_existing_ticket_for_same_request_id(self):
        db = self.SessionLocal()
        try:
            first = create_ticket_from_portfolio_lead(db, self.make_lead())
            second = create_ticket_from_portfolio_lead(db, self.make_lead(nome="Maria S."))

            self.assertEqual(first.id, second.id)
            self.assertEqual(db.query(type(first)).count(), 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
