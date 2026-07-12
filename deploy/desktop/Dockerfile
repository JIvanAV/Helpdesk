FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY deploy/desktop/backend/requirements.txt /app/deploy/desktop/backend/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/deploy/desktop/backend/requirements.txt

COPY deploy/desktop/backend /app/deploy/desktop/backend
COPY deploy/desktop/frontend /app/deploy/desktop/frontend

RUN mkdir -p /app/deploy/desktop/data

WORKDIR /app/deploy/desktop/backend

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
