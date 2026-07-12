"""Regression tests for Docker desktop deployment assets."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT_DIR / "deploy" / "desktop" / "Dockerfile"
COMPOSE_FILE = ROOT_DIR / "deploy" / "desktop" / "docker-compose.yml"
DOCKERIGNORE = ROOT_DIR / ".dockerignore"


def test_desktop_dockerfile_runs_fastapi_demo():
    content = DOCKERFILE.read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in content
    assert "deploy/desktop/backend/requirements.txt" in content
    assert "deploy/desktop/frontend" in content
    assert "EXPOSE 8001" in content
    assert '"uvicorn"' in content
    assert '"main:app"' in content
    assert '"0.0.0.0"' in content
    assert '"8001"' in content


def test_docker_compose_exposes_demo_with_persistent_data_volume():
    content = COMPOSE_FILE.read_text(encoding="utf-8")

    assert "ivan-helpdesk:" in content
    assert "dockerfile: deploy/desktop/Dockerfile" in content
    assert '"8001:8001"' in content
    assert "helpdesk-data:/app/deploy/desktop/data" in content
    assert "healthcheck:" in content
    assert "name: ivan-helpdesk-data" in content


def test_dockerignore_keeps_local_runtime_artifacts_out_of_image():
    content = DOCKERIGNORE.read_text(encoding="utf-8")

    assert ".git/" in content
    assert ".venv/" in content
    assert "deploy/desktop/data/*.db" in content
    assert "deploy/desktop/logs/" in content
