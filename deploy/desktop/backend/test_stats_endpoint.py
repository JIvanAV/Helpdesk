import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import TicketPriority, TicketStatus
from schemas import TicketCreate
from service import create_ticket


class HelpdeskStatsEndpointTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()
        self.addCleanup(self.db.close)

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)

    def create_case(self, title, priority, status=TicketStatus.ABERTO):
        ticket = create_ticket(
            self.db,
            TicketCreate(
                titulo=title,
                descricao="Caso usado para validar o resumo operacional.",
                categoria="Teste",
                prioridade=priority,
                solicitante_nome="José Ivan",
                solicitante_email="jose@example.com",
                solicitante_setor="helpdesk",
            ),
        )
        ticket.status = status
        self.db.commit()
        self.db.refresh(ticket)

    def test_stats_summary_counts_status_and_priority(self):
        self.create_case("Chamado aberto", TicketPriority.ALTA, TicketStatus.ABERTO)
        self.create_case("Chamado em andamento", TicketPriority.MEDIA, TicketStatus.EM_ANDAMENTO)
        self.create_case("Chamado resolvido", TicketPriority.MEDIA, TicketStatus.RESOLVIDO)

        response = self.client.get("/tickets/stats/summary")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(body["by_status"], {"ABERTO": 1, "EM_ANDAMENTO": 1, "RESOLVIDO": 1})
        self.assertEqual(body["by_priority"], {"ALTA": 1, "MEDIA": 2})


if __name__ == "__main__":
    unittest.main()
