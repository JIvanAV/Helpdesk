"""Integration tests for the local API and SPA frontend."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402
from database import init_db  # noqa: E402

init_db()

client = TestClient(app)


def test_health_reports_current_version():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["service"] == "ivan-helpdesk"
    assert payload["version"] == "0.3.0"


def test_home_serves_spa_frontend():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Ivan Helpdesk" in response.text
    assert "Novo chamado" in response.text
    assert "helpdeskApp" in response.text


def test_ticket_crud_flow_via_api():
    create_response = client.post(
        "/tickets",
        json={
            "title": "Notebook sem rede",
            "description": "Usuário relata que o notebook não conecta na rede corporativa.",
            "category": "network",
            "priority": "alta",
            "requester_name": "José Ivan",
            "requester_email": "joseivanabrantes@gmail.com",
            "requester_department": "TI",
        },
    )

    assert create_response.status_code == 201
    ticket = create_response.json()
    assert ticket["status"] == "aberto"
    assert ticket["category"] == "network"

    update_response = client.patch(
        f"/tickets/{ticket['id']}",
        json={"status": "resolvido", "resolution": "Driver de rede reinstalado e conexão validada."},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "resolvido"
    assert updated["resolved_at"] is not None

    stats_response = client.get("/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["total"] >= 1


def test_ticket_search_filter_matches_title_and_requester_email():
    first = client.post(
        "/tickets",
        json={
            "title": "Impressora fiscal travando",
            "description": "Fila de impressão para nota fiscal parou no setor financeiro.",
            "category": "hardware",
            "priority": "alta",
            "requester_name": "Maria Financeiro",
            "requester_email": "maria.financeiro@example.com",
        },
    )
    second = client.post(
        "/tickets",
        json={
            "title": "Acesso ao ERP",
            "description": "Usuário novo precisa de permissão inicial.",
            "category": "access",
            "priority": "media",
            "requester_name": "Carlos Operações",
            "requester_email": "carlos.ops@example.com",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

    title_response = client.get("/tickets?search=fiscal")
    assert title_response.status_code == 200
    title_payload = title_response.json()
    assert title_payload["total"] >= 1
    assert any(ticket["title"] == "Impressora fiscal travando" for ticket in title_payload["tickets"])

    email_response = client.get("/tickets?search=carlos.ops")
    assert email_response.status_code == 200
    email_payload = email_response.json()
    assert email_payload["total"] >= 1
    assert any(ticket["requester_email"] == "carlos.ops@example.com" for ticket in email_payload["tickets"])
