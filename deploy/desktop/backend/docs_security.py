import os
import logging
from hmac import compare_digest
from typing import Optional

from fastapi import Header, HTTPException, Query, status

DOCS_ACCESS_KEY_ENV = "HELPDESK_DOCS_KEY"
DOCS_ACCESS_HEADER = "X-Helpdesk-Docs-Key"
DEFAULT_LOCAL_DOCS_KEY = "local-dev-docs"
logger = logging.getLogger("ivan_helpdesk.docs_security")


def get_docs_access_key() -> str:
    """Return the simple key used to open the local API documentation.

    The fallback keeps the portfolio project easy to run on a clean machine,
    while production can override the key with HELPDESK_DOCS_KEY.
    """

    configured_key = os.getenv(DOCS_ACCESS_KEY_ENV, "").strip()
    return configured_key or DEFAULT_LOCAL_DOCS_KEY


def verify_docs_access(
    docs_key: Optional[str] = Query(default=None, alias="key"),
    header_key: Optional[str] = Header(..., alias=DOCS_ACCESS_HEADER),
) -> None:
    provided_key = header_key or docs_key or ""
    expected_key = get_docs_access_key()

    if not compare_digest(provided_key, expected_key):
        logger.warning("Tentativa bloqueada de acesso à documentação do Helpdesk")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave da documentação inválida ou ausente",
        )
