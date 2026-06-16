import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Ticket
from service import TicketService
from schemas import TicketCreate, TicketUpdate

# Setup in-memory DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_feedback_implementation(db):
    service = TicketService(db)
    
    # 1. Create a ticket
    ticket_data = TicketCreate(
        title="Teste Feedback",
        description="Descrição longa para teste",
        category="software",
        requester_name="José Ivan",
        requester_email="ivan@example.com"
    )
    ticket = service.create_ticket(ticket_data)
    
    # 2. Try to add feedback while 'aberto' (should fail)
    update_data = TicketUpdate(feedback=5)
    with pytest.raises(ValueError, match="Feedback só pode ser adicionado"):
        service.update_ticket(ticket.id, update_data)
        
    # 3. Resolve ticket
    service.update_ticket(ticket.id, TicketUpdate(status="resolvido"))
    
    # 4. Add feedback (should work)
    service.update_ticket(ticket.id, TicketUpdate(feedback=4))
    updated = service.get_ticket(ticket.id)
    assert updated.feedback == 4
    
    # 5. Invalid feedback score (should fail in schema validation)
    with pytest.raises(ValidationError):
        TicketUpdate(feedback=10)
