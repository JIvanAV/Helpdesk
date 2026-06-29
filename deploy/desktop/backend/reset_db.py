import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "../data/helpdesk.db"

def reset_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Limpa tickets
    cursor.execute("DELETE FROM tickets")
    
    # Insere chamado tutorial
    cursor.execute("""
        INSERT INTO tickets (title, description, category, priority, status, origin, requester_name, requester_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Tutorial: Como abrir chamados",
        "Bem-vindo ao Ivan Helpdesk! Este é um chamado de exemplo para mostrar como a interface funciona. Você pode abrir novos chamados preenchendo o formulário à esquerda.",
        "software",
        "baixa",
        "aberto",
        "portal",
        "Sistema",
        "tutorial@ivanhelpdesk.com"
    ))
    
    conn.commit()
    conn.close()
    print(f"Banco de dados em {DB_PATH} limpo e chamado tutorial inserido.")

if __name__ == "__main__":
    reset_db()
