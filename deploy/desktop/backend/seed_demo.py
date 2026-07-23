"""Recruiter-friendly demo data for the local Ivan Helpdesk presentation."""

from database import SessionLocal, init_db
from models import Ticket, TicketAuditEvent


DEMO_TICKETS = [
    {
        "title": "Computador da recepção não inicia",
        "description": "A máquina liga, mas fica travada na tela inicial antes do Windows carregar.",
        "category": "hardware",
        "priority": "alta",
        "impact": "alto",
        "status": "em_andamento",
        "support_level": "N2",
        "origin": "telefone",
        "requester_name": "Marina Recepção",
        "requester_email": "marina.recepcao@example.com",
        "requester_department": "Recepção",
        "assigned_to": "José Ivan",
        "internal_comments": "[comentário interno] Validar HD e memória antes de reinstalar o sistema.",
    },
    {
        "title": "Sistema financeiro indisponível",
        "description": "Equipe financeira não consegue acessar o sistema de pagamentos no fechamento do dia.",
        "category": "software",
        "priority": "critica",
        "impact": "parada_total",
        "status": "aberto",
        "support_level": "N2",
        "origin": "email",
        "requester_name": "Rafael Financeiro",
        "requester_email": "rafael.financeiro@example.com",
        "requester_department": "Financeiro",
        "assigned_to": "José Ivan",
    },
    {
        "title": "Impressora do setor fiscal não imprime",
        "description": "Fila de impressão acumula documentos, mas nenhum arquivo sai na impressora compartilhada.",
        "category": "hardware",
        "priority": "media",
        "impact": "medio",
        "status": "resolvido",
        "origin": "presencial",
        "requester_name": "Camila Fiscal",
        "requester_email": "camila.fiscal@example.com",
        "requester_department": "Fiscal",
        "assigned_to": "José Ivan",
        "resolution": "Driver reinstalado e fila de impressão limpa. Usuária validou impressão de teste.",
        "feedback": 5,
    },
    {
        "title": "Criar acesso para novo colaborador",
        "description": "Novo colaborador precisa de usuário para e-mail, sistema interno e pasta compartilhada.",
        "category": "access",
        "priority": "baixa",
        "impact": "baixo",
        "status": "aberto",
        "origin": "portal",
        "requester_name": "Ana RH",
        "requester_email": "ana.rh@example.com",
        "requester_department": "RH",
    },
]


def reset_recruiter_demo(db) -> list[Ticket]:
    """Replace local tickets with a small scenario made for portfolio demos."""
    db.query(TicketAuditEvent).delete()
    db.query(Ticket).delete()

    tickets = [Ticket(**ticket_data) for ticket_data in DEMO_TICKETS]
    db.add_all(tickets)
    db.commit()

    for ticket in tickets:
        db.refresh(ticket)
    return tickets


def seed_demo_data() -> None:
    """CLI helper used when preparing the desktop demo manually."""
    init_db()
    db = SessionLocal()
    try:
        tickets = reset_recruiter_demo(db)
        print(f"Demo de recrutador preparado com {len(tickets)} chamados.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
