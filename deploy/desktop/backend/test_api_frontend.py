"""Integration tests for the local API and SPA frontend."""

import sys
from pathlib import Path
from uuid import uuid4

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
    assert payload["version"] == "0.3.1"


def test_home_serves_spa_frontend():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Ivan Helpdesk" in response.text
    assert "Novo chamado" in response.text
    assert "Todas as categorias" in response.text
    assert "categoryFilter" in response.text
    assert "Todas as prioridades" in response.text
    assert "priorityFilter" in response.text
    assert "Limpar filtros" in response.text
    assert "Filtrar técnico" in response.text
    assert "assigneeFilter" in response.text
    assert "Técnico responsável" in response.text
    assert "Histórico de resolução" in response.text
    assert "Nova atualização da resolução" in response.text
    assert "resolution_note" in response.text
    assert "Formato esperado: nome@empresa.com" in response.text
    assert "pattern=\"[^@\\s]+@[^@\\s]+\\.[^@\\s]+\"" in response.text
    assert "helpdeskApp" in response.text
    assert "Exportar CSV" in response.text
    assert "/tickets/export.csv" in response.text


def test_ticket_export_csv_download_contains_created_ticket():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Exportacao CSV {run_marker}",
            "description": "Chamado usado para validar exportação CSV de relatórios.",
            "category": "software",
            "priority": "critica",
            "requester_name": "QA Exportacao",
            "requester_email": f"qa.export.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201

    response = client.get("/tickets/export.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "ivan-helpdesk-chamados.csv" in response.headers["content-disposition"]
    assert "id;titulo;categoria;prioridade;status" in response.text
    assert f"Exportacao CSV {run_marker}" in response.text
    assert f"qa.export.{run_marker}@example.com" in response.text


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


def test_ticket_resolution_updates_are_appended_as_history():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Historico resolucao {run_marker}",
            "description": "Chamado usado para validar histórico de resolução.",
            "category": "software",
            "priority": "media",
            "requester_name": "QA Historico",
            "requester_email": f"qa.history.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    first = client.patch(
        f"/tickets/{ticket_id}",
        json={"status": "em_andamento", "resolution": "Primeira análise registrada."},
    )
    second = client.patch(
        f"/tickets/{ticket_id}",
        json={"status": "resolvido", "resolution": "Solução final aplicada."},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    resolution = second.json()["resolution"]
    assert "Primeira análise registrada." in resolution
    assert "Solução final aplicada." in resolution
    assert resolution.index("Primeira análise registrada.") < resolution.index("Solução final aplicada.")


def test_ticket_assignee_can_be_updated_and_filtered():
    run_marker = uuid4().hex[:8]
    assigned = client.post(
        "/tickets",
        json={
            "title": f"Triagem com tecnico {run_marker}",
            "description": "Chamado usado para validar atribuição de técnico responsável.",
            "category": "hardware",
            "priority": "alta",
            "requester_name": "QA Atribuicao",
            "requester_email": f"qa.assigned.{run_marker}@example.com",
        },
    )
    unassigned = client.post(
        "/tickets",
        json={
            "title": f"Controle sem tecnico {run_marker}",
            "description": "Chamado controle para garantir que o filtro exclui outros responsáveis.",
            "category": "hardware",
            "priority": "media",
            "requester_name": "QA Atribuicao",
            "requester_email": f"qa.unassigned.{run_marker}@example.com",
        },
    )

    assert assigned.status_code == 201
    assert unassigned.status_code == 201

    ticket_id = assigned.json()["id"]
    update_response = client.patch(
        f"/tickets/{ticket_id}",
        json={"assigned_to": "Ivan Suporte", "status": "em_andamento"},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["assigned_to"] == "Ivan Suporte"
    assert updated["status"] == "em_andamento"

    response = client.get(f"/tickets?assigned_to=ivan%20suporte&search={run_marker}&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["tickets"][0]["id"] == ticket_id
    assert payload["tickets"][0]["assigned_to"] == "Ivan Suporte"


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


def test_ticket_category_filter_returns_only_selected_category():
    hardware = client.post(
        "/tickets",
        json={
            "title": "Mouse USB com falha intermitente",
            "description": "Periférico desconecta durante o atendimento no balcão.",
            "category": "hardware",
            "priority": "media",
            "requester_name": "Ana Estoque",
            "requester_email": "ana.hardware@example.com",
        },
    )
    software = client.post(
        "/tickets",
        json={
            "title": "Sistema de notas sem abrir",
            "description": "Aplicação exibe erro ao inicializar no setor fiscal.",
            "category": "software",
            "priority": "alta",
            "requester_name": "Bruno Fiscal",
            "requester_email": "bruno.software@example.com",
        },
    )

    assert hardware.status_code == 201
    assert software.status_code == 201

    response = client.get("/tickets?category=hardware&search=example.com&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert all(ticket["category"] == "hardware" for ticket in payload["tickets"])
    assert any(ticket["requester_email"] == "ana.hardware@example.com" for ticket in payload["tickets"])
    assert not any(ticket["requester_email"] == "bruno.software@example.com" for ticket in payload["tickets"])


def test_ticket_priority_filter_returns_only_selected_priority():
    run_marker = f"Filtro prioridade {uuid4().hex[:8]}"
    high = client.post(
        "/tickets",
        json={
            "title": f"{run_marker} alta",
            "description": "Chamado importante usado para validar filtro de prioridade no dashboard.",
            "category": "software",
            "priority": "alta",
            "requester_name": "QA Prioridade",
            "requester_email": f"qa.alta.{run_marker.split()[-1]}@example.com",
        },
    )
    low = client.post(
        "/tickets",
        json={
            "title": f"{run_marker} baixa",
            "description": "Chamado simples usado como controle negativo do filtro de prioridade.",
            "category": "software",
            "priority": "baixa",
            "requester_name": "QA Prioridade",
            "requester_email": f"qa.baixa.{run_marker.split()[-1]}@example.com",
        },
    )

    assert high.status_code == 201
    assert low.status_code == 201

    response = client.get(f"/tickets?priority=alta&search={run_marker.replace(' ', '%20')}&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["tickets"][0]["priority"] == "alta"
    assert payload["tickets"][0]["title"].endswith("alta")


def test_ticket_priority_sort_orders_urgent_items_first():
    run_marker = f"Ordenacao urgente {uuid4().hex[:8]}"
    cases = [
        ("baixa", f"{run_marker} baixa"),
        ("critica", f"{run_marker} critica"),
        ("media", f"{run_marker} media"),
        ("alta", f"{run_marker} alta"),
    ]

    for priority, title in cases:
        response = client.post(
            "/tickets",
            json={
                "title": title,
                "description": "Chamado usado para validar ordenação por prioridade no dashboard.",
                "category": "software",
                "priority": priority,
                "requester_name": "QA Portfolio",
                "requester_email": f"qa.{priority}.{run_marker.split()[-1]}@example.com",
            },
        )
        assert response.status_code == 201

    response = client.get(f"/tickets?search={run_marker.replace(' ', '%20')}&sort=priority&page_size=10")

    assert response.status_code == 200
    payload = response.json()
    ordered_priorities = [ticket["priority"] for ticket in payload["tickets"]]
    assert ordered_priorities == ["critica", "alta", "media", "baixa"]


def test_security_headers_are_applied_to_frontend_and_api():
    frontend_response = client.get("/")
    api_response = client.get("/health")

    for response in (frontend_response, api_response):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["permissions-policy"] == "geolocation=(), microphone=(), camera=()"


def test_cors_rejects_unknown_origins_and_allows_localhost():
    blocked = client.options(
        "/tickets",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    allowed = client.options(
        "/tickets",
        headers={
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "access-control-allow-origin" not in blocked.headers
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:8000"


def test_validation_errors_return_safe_generic_payload():
    response = client.post(
        "/tickets",
        json={
            "title": "Oi",
            "description": "curta",
            "category": "software",
            "priority": "media",
            "requester_name": "J",
            "requester_email": "email-invalido",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"] == "validation_error"
    assert payload["detail"] == "Verifique os campos enviados e tente novamente."
    assert "request_id" in payload
    assert "email-invalido" not in response.text
