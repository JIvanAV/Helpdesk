"""Category-based support checklist suggestions for Ivan Helpdesk."""

from __future__ import annotations


KNOWLEDGE_BASE = {
    "hardware": {
        "label": "Hardware",
        "summary": "Verificações físicas e periféricos antes de escalonar.",
        "steps": [
            "Confirmar energia, cabos e tomada do equipamento.",
            "Testar periféricos em outra porta ou máquina.",
            "Registrar número de patrimônio e sintomas observados.",
        ],
    },
    "software": {
        "label": "Software",
        "summary": "Triagem de aplicação, versão e mensagem de erro.",
        "steps": [
            "Identificar sistema, versão e usuário afetado.",
            "Reproduzir o erro e coletar mensagem ou print.",
            "Validar atualização, permissões e reinício controlado.",
        ],
    },
    "network": {
        "label": "Rede",
        "summary": "Conectividade básica para chamados de internet/rede local.",
        "steps": [
            "Verificar cabo, Wi-Fi e link do switch/roteador.",
            "Testar ping para gateway e serviço afetado.",
            "Validar IP, DNS e alcance de outros usuários no setor.",
        ],
    },
    "access": {
        "label": "Acesso",
        "summary": "Contas, permissões e bloqueios de usuário.",
        "steps": [
            "Confirmar usuário, sistema e perfil de acesso solicitado.",
            "Verificar bloqueio, expiração de senha e grupos/permissões.",
            "Registrar aprovação do responsável antes de liberar acesso.",
        ],
    },
    "other": {
        "label": "Outro",
        "summary": "Coleta mínima para classificar e direcionar o chamado.",
        "steps": [
            "Descrever impacto, setor e horário de início do problema.",
            "Anexar evidências sem senhas ou dados sensíveis.",
            "Reclassificar a categoria após a primeira análise técnica.",
        ],
    },
}


def list_checklists() -> dict[str, dict[str, object]]:
    """Return all support checklists keyed by ticket category."""
    return KNOWLEDGE_BASE


def get_checklist(category: str) -> dict[str, object] | None:
    """Return a checklist for a single category, if it exists."""
    return KNOWLEDGE_BASE.get(category)
