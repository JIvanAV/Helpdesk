import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "../data/helpdesk.db"

def seed_demo_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Limpa dados existentes para garantir o estado limpo
    cursor.execute("DELETE FROM tickets")
    
    # Dados de exemplo para o recrutador
    demo_tickets = [
        ("Login não funciona", "Técnico reportou que o login está dando erro 403 no ambiente de produção.", "hardware", "alta", "aberto", "telefone", "Técnico João", "joao@exemplo.com"),
        ("Impressora travada", "Impressora da recepção não responde aos comandos de impressão.", "hardware", "media", "aberto", "email", "Maria Recepção", "maria@exemplo.com"),
        ("Acesso ao sistema falhando", "Erro ao tentar autenticar no sistema de pagamentos.", "software", "parada_total", "aberto", "chat", "Gestor Financeiro", "gestor@exemplo.com")
    ]
    
    cursor.executemany("""
        INSERT INTO tickets (title, description, category, priority, status, origin, requester_name, requester_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_tickets)
    
    conn.commit()
    conn.close()
    print("Dados de demonstração inseridos com sucesso.")

if __name__ == "__main__":
    seed_demo_data()
