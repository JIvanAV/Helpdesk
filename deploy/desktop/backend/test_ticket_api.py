import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


class HelpdeskTicketApiTest(unittest.TestCase):
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

    def make_payload(self, **overrides):
        payload = {
            "titulo": "Notebook lento para atendimento",
            "descricao": "Usuário precisa de diagnóstico remoto antes de formatar.",
            "categoria": "Suporte remoto",
            "prioridade": "ALTA",
            "solicitante_nome": "Maria Silva",
            "solicitante_email": "maria@example.com",
            "solicitante_setor": "portfolio",
        }
        payload.update(overrides)
        return payload

    def test_creates_ticket_with_default_open_status(self):
        response = self.client.post("/tickets", json=self.make_payload())

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["titulo"], "Notebook lento para atendimento")
        self.assertEqual(body["status"], "ABERTO")
        self.assertEqual(body["prioridade"], "ALTA")
        self.assertEqual(body["solicitante_setor"], "portfolio")

    def test_lists_created_tickets_with_total(self):
        self.client.post("/tickets", json=self.make_payload(titulo="Primeiro chamado"))
        self.client.post("/tickets", json=self.make_payload(titulo="Segundo chamado"))

        response = self.client.get("/tickets")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["size"], 100)
        self.assertEqual(len(body["tickets"]), 2)

    def test_filters_ticket_list_by_priority(self):
        self.client.post("/tickets", json=self.make_payload(titulo="Alta", prioridade="ALTA"))
        self.client.post("/tickets", json=self.make_payload(titulo="Baixa", prioridade="BAIXA"))

        response = self.client.get("/tickets?prioridade=ALTA")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["tickets"][0]["titulo"], "Alta")


if __name__ == "__main__":
    unittest.main()
