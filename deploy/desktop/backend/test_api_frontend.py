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
    assert payload["version"] == "0.3.10"


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
    assert "Assumir chamado" in response.text
    assert "assumeTicket(ticket)" in response.text
    assert "José Ivan" in response.text
    assert "Comentários do técnico" in response.text
    assert "histórico cumulativo" in response.text
    assert "Novo comentário do técnico" in response.text
    assert "resolution_note" in response.text
    assert "Formato esperado: nome@empresa.com" in response.text
    assert "pattern=\"[^@\\s]+@[^@\\s]+\\.[^@\\s]+\"" in response.text
    assert "helpdeskApp" in response.text
    assert "Exportar CSV" in response.text
    assert "/tickets/export.csv" in response.text
    assert "Origem do chamado" in response.text
    assert "originFilter" in response.text
    assert "Todas as origens" in response.text
    assert "toggleTheme()" in response.text
    assert "ivan-helpdesk-theme" in response.text
    assert "localStorage.setItem" in response.text
    assert ":aria-pressed=\"darkMode.toString()\"" in response.text
    assert "Resumo executivo" in response.text
    assert "executiveSummaryItems" in response.text
    assert "Panorama rápido da operação" in response.text
    assert "Tempo médio" in response.text
    assert "avgResolutionLabel" in response.text
    assert "avg_resolution_hours" in response.text
    assert "Atrasados" in response.text
    assert "by_sla_status" in response.text
    assert "SLA: No prazo" in response.text
    assert "slaBadge" in response.text
    assert "slaLabel(ticket.sla_status)" in response.text
    assert "Timeline do chamado" in response.text
    assert "ticket.timeline?.length" in response.text
    assert "formatDateTime(event.occurred_at)" in response.text
    assert "Base de conhecimento sugerida" in response.text
    assert "Checklist sugerido da base de conhecimento" in response.text
    assert "selectedChecklist" in response.text
    assert "loadKnowledgeBase" in response.text
    assert "Sessão do técnico" in response.text
    assert "technicianSession" in response.text
    assert "ivan-helpdesk-technician" in response.text
    assert "ticket.assigned_to = this.currentTechnician" in response.text
    assert "buildTicketQuery" in response.text
    assert "editableTicket" in response.text
    assert "assigned_to: ticket.assigned_to || this.currentTechnician" in response.text
    assert "Perfil de acesso" in response.text
    assert "ivan-helpdesk-role" in response.text
    assert "SESSION_KEYS" in response.text
    assert "authStorage" in response.text
    assert "DEFAULT_TECHNICIAN_SESSION" in response.text
    assert "technicianSession.role" in response.text
    assert "Entrar como técnico" in response.text
    assert "Sair da sessão" in response.text
    assert "logoutTechnician" in response.text
    assert "sem senha real" in response.text
    assert "Demo seguro" in response.text
    assert "Comentários internos do chamado" in response.text
    assert "Comentário interno para a equipe técnica" in response.text
    assert "addInternalComment(ticket)" in response.text
    assert "/comments" in response.text
    assert "Histórico de alterações do chamado" in response.text
    assert "ticket.audit_events?.length" in response.text
    assert "loadTicketAudit" in response.text
    assert "/audit" in response.text
    assert "auditTypeLabel" in response.text
    assert "auditChangeSummary" in response.text


def test_knowledge_base_endpoint_returns_category_checklists():
    response = client.get("/knowledge-base")

    assert response.status_code == 200
    categories = response.json()["categories"]
    assert "network" in categories
    assert categories["network"]["label"] == "Rede"
    assert any("ping" in step.lower() for step in categories["network"]["steps"])
    assert "access" in categories
    assert "permissões" in " ".join(categories["access"]["steps"]).lower()

    single = client.get("/knowledge-base/hardware")
    assert single.status_code == 200
    assert single.json()["label"] == "Hardware"


def test_ticket_export_csv_download_contains_created_ticket():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Exportacao CSV {run_marker}",
            "description": "Chamado usado para validar exportação CSV de relatórios.",
            "category": "software",
            "priority": "critica",
            "origin": "whatsapp",
            "requester_name": "QA Exportacao",
            "requester_email": f"qa.export.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201

    response = client.get("/tickets/export.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "ivan-helpdesk-chamados.csv" in response.headers["content-disposition"]
    assert "id;titulo;categoria;prioridade;impacto;status;origem" in response.text
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
    stats_payload = stats_response.json()
    assert stats_payload["total"] >= 1
    assert stats_payload["today"]["created"] >= 1
    assert "resolved" in stats_payload["today"]
    assert "avg_resolution_hours" in stats_payload
    assert isinstance(stats_payload["avg_resolution_hours"], int | float)
    assert stats_payload["avg_resolution_hours"] >= 0
    assert "by_sla_status" in stats_payload
    assert "no_prazo" in stats_payload["by_sla_status"]


def test_ticket_response_includes_sla_status():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"SLA visual {run_marker}",
            "description": "Chamado usado para validar classificação visual de SLA.",
            "category": "network",
            "priority": "alta",
            "requester_name": "QA SLA",
            "requester_email": f"qa.sla.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["sla_status"] == "no_prazo"

    ticket_response = client.get(f"/tickets/{payload['id']}")
    assert ticket_response.status_code == 200
    assert ticket_response.json()["sla_status"] == "no_prazo"


def test_ticket_response_includes_computed_timeline_events():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Timeline chamado {run_marker}",
            "description": "Chamado usado para validar timeline calculada do atendimento.",
            "category": "access",
            "priority": "alta",
            "requester_name": "QA Timeline",
            "requester_email": f"qa.timeline.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["timeline"][0]["label"] == "Chamado criado"
    assert "QA Timeline" in created["timeline"][0]["description"]

    update_response = client.patch(
        f"/tickets/{created['id']}",
        json={
            "status": "resolvido",
            "assigned_to": "José Ivan",
            "resolution": "Acesso revisado, permissão corrigida e usuário validou o login.",
        },
    )

    assert update_response.status_code == 200
    timeline = update_response.json()["timeline"]
    labels = [event["label"] for event in timeline]
    assert "Chamado criado" in labels
    assert "Técnico atribuído" in labels
    assert "Chamado atualizado" in labels
    assert "Chamado resolvido" in labels
    assert any("José Ivan" in event["description"] for event in timeline)
    assert all("occurred_at" in event for event in timeline)


def test_ticket_internal_comments_are_appended_without_overwriting():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Comentario interno {run_marker}",
            "description": "Chamado usado para validar comentarios internos do tecnico.",
            "category": "software",
            "priority": "media",
            "requester_name": "QA Comentario",
            "requester_email": f"qa.comment.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    first = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"technician": "Ivan Suporte", "comment": "Coletar evidência do erro antes de fechar."},
    )
    second = client.patch(
        f"/tickets/{ticket_id}",
        json={"internal_comment": "Usuário disponível apenas pela manhã.", "assigned_to": "Ivan Suporte"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    payload = second.json()
    assert payload["internal_comment_count"] == 2
    assert "Coletar evidência do erro antes de fechar." in payload["internal_comments"]
    assert "Usuário disponível apenas pela manhã." in payload["internal_comments"]
    assert "[comentário interno] Ivan Suporte" in payload["internal_comments"]
    assert "---" in payload["internal_comments"]


def test_ticket_audit_history_records_update_flow():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Auditoria chamado {run_marker}",
            "description": "Chamado usado para validar histórico de alterações auditável.",
            "category": "access",
            "priority": "media",
            "requester_name": "QA Auditoria",
            "requester_email": f"qa.audit.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201
    ticket_id = create_response.json()["id"]

    empty_history = client.get(f"/tickets/{ticket_id}/audit")
    assert empty_history.status_code == 200
    assert empty_history.json() == []

    update_response = client.patch(
        f"/tickets/{ticket_id}",
        json={
            "status": "em_andamento",
            "priority": "alta",
            "assigned_to": "Ivan Suporte",
            "resolution": "Primeira investigação registrada para auditoria.",
        },
    )
    comment_response = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"technician": "Ivan Suporte", "comment": "Evidência coletada antes do fechamento."},
    )

    assert update_response.status_code == 200
    assert comment_response.status_code == 200

    history_response = client.get(f"/tickets/{ticket_id}/audit")
    assert history_response.status_code == 200
    events = history_response.json()
    descriptions = [event["description"] for event in events]
    event_types = [event["event_type"] for event in events]

    assert len(events) >= 4
    assert "field_change" in event_types
    assert "resolution" in event_types
    assert "internal_comment" in event_types
    assert any("Status alterado de 'aberto' para 'em_andamento'" in item for item in descriptions)
    assert any("Prioridade alterado de 'media' para 'alta'" in item for item in descriptions)
    assert any("Responsável alterado de 'não informado' para 'Ivan Suporte'" in item for item in descriptions)
    assert all(event["ticket_id"] == ticket_id for event in events)
    assert all("created_at" in event for event in events)

    status_event = next(event for event in events if event["field_name"] == "status")
    assert status_event["previous_value"] == "aberto"
    assert status_event["new_value"] == "em_andamento"
    assert status_event["actor_role"] == "tecnico"

    assignment_events = client.get(f"/tickets/{ticket_id}/audit?event_type=assignment&technician=ivan%20suporte")
    assert assignment_events.status_code == 200
    assert len(assignment_events.json()) == 1
    assert assignment_events.json()[0]["field_name"] == "assigned_to"

    limited_history = client.get(f"/tickets/{ticket_id}/audit?limit=2")
    assert limited_history.status_code == 200
    assert len(limited_history.json()) == 2

    missing_history = client.get("/tickets/999999999/audit")
    assert missing_history.status_code == 404


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
        json={"status": "em_andamento", "assigned_to": "Ivan Suporte", "resolution": "Primeira análise registrada."},
    )
    second = client.patch(
        f"/tickets/{ticket_id}",
        json={"status": "resolvido", "assigned_to": "Ivan Suporte", "resolution": "Solução final aplicada."},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    resolution = second.json()["resolution"]
    assert "Primeira análise registrada." in resolution
    assert "Solução final aplicada." in resolution
    assert "Ivan Suporte" in resolution
    assert "UTC" in resolution
    assert "---" in resolution
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


def test_ticket_origin_can_be_created_updated_filtered_and_reported():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Origem WhatsApp {run_marker}",
            "description": "Chamado usado para validar origem do atendimento.",
            "category": "software",
            "priority": "media",
            "origin": "whatsapp",
            "requester_name": "QA Origem",
            "requester_email": f"qa.origin.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201
    ticket = create_response.json()
    assert ticket["origin"] == "whatsapp"

    update_response = client.patch(f"/tickets/{ticket['id']}", json={"origin": "telefone"})
    assert update_response.status_code == 200
    assert update_response.json()["origin"] == "telefone"

    filter_response = client.get(f"/tickets?origin=telefone&search={run_marker}&page_size=20")
    assert filter_response.status_code == 200
    payload = filter_response.json()
    assert payload["total"] == 1
    assert payload["tickets"][0]["id"] == ticket["id"]

    stats_response = client.get("/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["by_origin"]["telefone"] >= 1


def test_ticket_impact_can_be_created_updated_filtered_and_reported():
    run_marker = uuid4().hex[:8]
    create_response = client.post(
        "/tickets",
        json={
            "title": f"Impacto operacional {run_marker}",
            "description": "Chamado usado para validar impacto operacional separado da prioridade.",
            "category": "network",
            "priority": "alta",
            "impact": "alto",
            "requester_name": "QA Impacto",
            "requester_email": f"qa.impact.{run_marker}@example.com",
        },
    )

    assert create_response.status_code == 201
    ticket = create_response.json()
    assert ticket["impact"] == "alto"

    update_response = client.patch(f"/tickets/{ticket['id']}", json={"impact": "parada_total"})
    assert update_response.status_code == 200
    assert update_response.json()["impact"] == "parada_total"

    filter_response = client.get(f"/tickets?impact=parada_total&search={run_marker}&page_size=20")
    assert filter_response.status_code == 200
    payload = filter_response.json()
    assert payload["total"] == 1
    assert payload["tickets"][0]["id"] == ticket["id"]

    stats_response = client.get("/stats")
    assert stats_response.status_code == 200
    assert stats_response.json()["by_impact"]["parada_total"] >= 1

    audit_response = client.get(f"/tickets/{ticket['id']}/audit")
    assert audit_response.status_code == 200
    descriptions = [event["description"] for event in audit_response.json()]
    assert any("Impacto operacional alterado de 'alto' para 'parada_total'" in item for item in descriptions)

    frontend_response = client.get("/")
    assert frontend_response.status_code == 200
    assert "Impacto operacional" in frontend_response.text
    assert "Todos os impactos" in frontend_response.text
