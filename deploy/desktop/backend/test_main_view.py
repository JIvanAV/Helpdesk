import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app
from models import TicketPriority, TicketStatus
from schemas import TicketCreate
from service import create_ticket


class HelpdeskMainViewTest(unittest.TestCase):
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

        from database import get_db

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app)

    def create_case(self, title, origin, status, priority):
        ticket = create_ticket(
            self.db,
            TicketCreate(
                titulo=title,
                descricao=f"Caso de teste para {origin}",
                categoria=f"Origem {origin}",
                prioridade=priority,
                solicitante_nome="José Ivan",
                solicitante_email="jose@example.com",
                solicitante_setor=origin,
            ),
        )
        ticket.status = status
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def test_home_view_filters_cases_by_query_string(self):
        self.create_case("Lead do portfólio", "portfolio", TicketStatus.ABERTO, TicketPriority.ALTA)
        self.create_case("Rotina de vagas", "automacao", TicketStatus.ABERTO, TicketPriority.MEDIA)
        self.create_case("Caso encerrado", "portfolio", TicketStatus.FECHADO, TicketPriority.ALTA)

        response = self.client.get("/?origin=portfolio&status=ABERTO&priority=ALTA")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Lead do portfólio", response.text)
        self.assertNotIn("Rotina de vagas", response.text)
        self.assertNotIn("Caso encerrado", response.text)


if __name__ == "__main__":
    unittest.main()
