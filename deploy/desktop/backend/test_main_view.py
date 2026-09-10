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

    def test_home_view_renders_filter_controls(self):
        self.create_case("Lead do portfólio", "portfolio", TicketStatus.ABERTO, TicketPriority.ALTA)
        self.create_case("Rotina de vagas", "automacao", TicketStatus.EM_ANDAMENTO, TicketPriority.MEDIA)

        response = self.client.get("/?origin=portfolio&status=ABERTO&priority=ALTA")

        self.assertEqual(response.status_code, 200)
        self.assertIn('aria-label="Filtros dos casos"', response.text)
        self.assertIn('<option value="portfolio" selected>portfolio</option>', response.text)
        self.assertIn('<option value="ABERTO" selected>ABERTO</option>', response.text)
        self.assertIn('<option value="ALTA" selected>ALTA</option>', response.text)
        self.assertIn('href="/"', response.text)

    def test_home_view_explains_when_filters_have_no_results(self):
        self.create_case("Lead do portfólio", "portfolio", TicketStatus.ABERTO, TicketPriority.ALTA)

        response = self.client.get("/?origin=automacao")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Nenhum caso encontrado com estes filtros", response.text)
        self.assertIn("Exibindo 0 de 1 casos", response.text)


if __name__ == "__main__":
    unittest.main()
