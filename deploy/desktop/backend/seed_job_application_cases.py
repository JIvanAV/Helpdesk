"""Seed helpdesk cases from José Ivan's job-application batch.

This script resets the current helpdesk tickets and creates 10 follow-up cases:
5 LinkedIn opportunities and 5 Gupy opportunities selected for José's
TI/support/backend profile.

Important: the automation log only confirms a local test cycle. It does not contain
external protocol numbers from LinkedIn/Gupy, so each case records the conclusion
status as "processed in automation test; external confirmation pending".
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "helpdesk.db"
NOW = datetime.utcnow().isoformat(sep=" ", timespec="seconds")

CASES = [
    {
        "titulo": "LinkedIn: RPE - Analista de Suporte NOC N1 JR",
        "categoria": "Candidatura LinkedIn / Suporte NOC",
        "prioridade": "CRITICA",
        "status": "ABERTO",
        "setor": "LinkedIn",
        "responsavel": "Hermes Agent",
        "link": "https://br.linkedin.com/jobs/view/analista-de-suporte-noc-n1-jr-at-rpe-4416923631",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte NOC/N1 júnior em João Pessoa, aderente ao perfil de suporte/TI e região-alvo.",
    },
    {
        "titulo": "LinkedIn: RPE - Analista de Suporte N1 JR",
        "categoria": "Candidatura LinkedIn / Suporte N1",
        "prioridade": "CRITICA",
        "status": "ABERTO",
        "setor": "LinkedIn",
        "responsavel": "Hermes Agent",
        "link": "https://br.linkedin.com/jobs/view/analista-de-suporte-n1-jr-at-rpe-4420997650",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte N1 júnior em João Pessoa, uma das melhores opções regionais para entrada rápida.",
    },
    {
        "titulo": "LinkedIn: Compass UOL - Analista de Suporte Junior Remote",
        "categoria": "Candidatura LinkedIn / Suporte Remoto",
        "prioridade": "ALTA",
        "status": "ABERTO",
        "setor": "LinkedIn",
        "responsavel": "Hermes Agent",
        "link": "https://br.linkedin.com/jobs/view/analista-de-suporte-junior-remote-at-compass-uol-4417311897",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte júnior remoto em empresa grande, boa para currículo e aderente a atendimento/suporte.",
    },
    {
        "titulo": "LinkedIn: CRM DataCrazy - Suporte Técnico N2 Remoto",
        "categoria": "Candidatura LinkedIn / Suporte Técnico",
        "prioridade": "ALTA",
        "status": "ABERTO",
        "setor": "LinkedIn",
        "responsavel": "Hermes Agent",
        "link": "https://br.linkedin.com/jobs/view/suporte-t%C3%A9cnico-n2-remoto-at-crm-datacrazy-4414026720",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte técnico remoto; N2 pode exigir mais experiência, mas aproveita vivência com infraestrutura e atendimento.",
    },
    {
        "titulo": "LinkedIn: BairesDev - Analista de Suporte de TI Remoto",
        "categoria": "Candidatura LinkedIn / Suporte Remoto",
        "prioridade": "ALTA",
        "status": "ABERTO",
        "setor": "LinkedIn",
        "responsavel": "Hermes Agent",
        "link": "https://br.linkedin.com/jobs/view/analista-de-suporte-de-ti-trabalho-remoto-ref%23282223-at-bairesdev-4157638879",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte de TI remoto, alinhado ao perfil técnico e possibilidade de vaga nacional.",
    },
    {
        "titulo": "Gupy: Nexdom Healthtech - Assistente de Suporte a Sistemas",
        "categoria": "Candidatura Gupy / Suporte a Sistemas",
        "prioridade": "ALTA",
        "status": "ABERTO",
        "setor": "Gupy",
        "responsavel": "Hermes Agent",
        "link": "https://vempranexdom.gupy.io/jobs/11309835?jobBoardSource=gupy_public_page",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte a sistemas remoto e efetivo, bom encaixe para helpdesk/suporte técnico.",
    },
    {
        "titulo": "Gupy: Nexdom Healthtech - Analista de Suporte Sistemas Junior",
        "categoria": "Candidatura Gupy / Suporte Júnior",
        "prioridade": "ALTA",
        "status": "ABERTO",
        "setor": "Gupy",
        "responsavel": "Hermes Agent",
        "link": "https://vempranexdom.gupy.io/jobs/11338152?jobBoardSource=gupy_public_page",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Cargo júnior de suporte a sistemas, remoto e compatível com experiência de atendimento técnico.",
    },
    {
        "titulo": "Gupy: Omie/G-Click - Analista de Suporte Técnico Júnior",
        "categoria": "Candidatura Gupy / Suporte Técnico",
        "prioridade": "ALTA",
        "status": "ABERTO",
        "setor": "Gupy",
        "responsavel": "Hermes Agent",
        "link": "https://carreirasomie.gupy.io/jobs/11468701?jobBoardSource=gupy_public_page",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte técnico júnior remoto em empresa de software, forte aderência ao currículo de TI.",
    },
    {
        "titulo": "Gupy: RPE - Analista de Suporte N1 JR",
        "categoria": "Candidatura Gupy / Suporte N1",
        "prioridade": "CRITICA",
        "status": "ABERTO",
        "setor": "Gupy",
        "responsavel": "Hermes Agent",
        "link": "https://rpe.gupy.io/jobs/11027288?jobBoardSource=gupy_public_page",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Suporte N1 júnior em João Pessoa, muito alinhado com TI/suporte e região-alvo.",
    },
    {
        "titulo": "Gupy: Hapvida - Assistente Informática",
        "categoria": "Candidatura Gupy / Informática",
        "prioridade": "ALTA",
        "status": "ABERTO",
        "setor": "Gupy",
        "responsavel": "Hermes Agent",
        "link": "https://hapvidandi.gupy.io/jobs/11416992?jobBoardSource=gupy_public_page",
        "curriculo": "José Ivan TI.pdf",
        "conclusao": "Processada no teste de automação; confirmação externa/protocolo ainda pendente.",
        "motivo": "Informática/suporte presencial em João Pessoa; boa vaga para perfil técnico hospitalar/TI.",
    },
]


def description(case: dict[str, str]) -> str:
    return "\n".join(
        [
            f"Link da vaga: {case['link']}",
            f"Currículo recomendado: {case['curriculo']}",
            f"Status de conclusão: {case['conclusao']}",
            f"Motivo da seleção: {case['motivo']}",
            "Próximo passo: abrir a plataforma, confirmar candidatura real, capturar comprovante/status e atualizar este caso.",
        ]
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tickets")
        sequence_table = cur.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sqlite_sequence'"
        ).fetchone()
        if sequence_table:
            cur.execute("DELETE FROM sqlite_sequence WHERE name = 'tickets'")
        for case in CASES:
            cur.execute(
                """
                INSERT INTO tickets (
                    titulo, descricao, status, prioridade, categoria,
                    solicitante_nome, solicitante_email, solicitante_setor,
                    tecnico_responsavel, created_at, updated_at, closed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    case["titulo"],
                    description(case),
                    case["status"],
                    case["prioridade"],
                    case["categoria"],
                    "José Ivan Abrantes Virgínio",
                    "joseivanabrantes@gmail.com",
                    case["setor"],
                    case["responsavel"],
                    NOW,
                    NOW,
                ),
            )
        conn.commit()
        total = cur.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    print(f"{total} casos recriados em {DB_PATH}")


if __name__ == "__main__":
    main()
