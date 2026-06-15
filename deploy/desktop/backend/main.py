"""Ivan Helpdesk API - Placeholder (Day 1)

This is a temporary entrypoint while the full backend is being built.
Days 2-3 will implement the complete REST API with SQLAlchemy models.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Ivan Helpdesk API",
    version="0.1.0-dev",
    description="Sistema de helpdesk para portfólio — Em desenvolvimento (Day 1/10)"
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ivan Helpdesk API</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>* { font-family: 'Inter', sans-serif; }</style>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen flex items-center justify-center p-8">
        <div class="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 md:p-12 text-center">
            <div class="w-20 h-20 mx-auto mb-6 bg-blue-100 rounded-2xl flex items-center justify-center">
                <svg class="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
            </div>
            <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Ivan Helpdesk API</h1>
            <p class="text-gray-500 mb-8 text-lg">Sistema de chamados para portfólio de TI/Suporte/Backend</p>

            <div class="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8 text-left">
                <h2 class="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                    <span class="bg-blue-600 text-white text-xs px-2 py-0.5 rounded">Day 1/10</span>
                    Status do Projeto
                </h2>
                <ul class="space-y-2 text-sm text-blue-700">
                    <li class="flex items-center gap-2">✅ <strong>Database:</strong> SQLAlchemy + SQLite configurado</li>
                    <li class="flex items-center gap-2">✅ <strong>Dependências:</strong> FastAPI, Uvicorn, Pydantic, etc.</li>
                    <li class="flex items-center gap-2">⏳ <strong>Models/Schemas:</strong> Dia 2</li>
                    <li class="flex items-center gap-2">⏳ <strong>CRUD API:</strong> Dia 3</li>
                    <li class="flex items-center gap-2">⏳ <strong>Frontend SPA:</strong> Dia 4</li>
                    <li class="flex items-center gap-2">⏳ <strong>Serviço Windows:</strong> Dia 6</li>
                </ul>
            </div>

            <div class="space-y-3">
                <a href="/docs" target="_blank"
                   class="inline-block w-full py-3 px-6 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors">
                    📖 Ver Documentação da API (Swagger UI)
                </a>
                <a href="/health"
                   class="inline-block w-full py-3 px-6 bg-gray-100 text-gray-700 font-semibold rounded-lg hover:bg-gray-200 transition-colors">
                    🏥 Health Check
                </a>
            </div>

            <p class="mt-8 text-xs text-gray-400">
                Deploy local: <code class="bg-gray-100 px-1.5 py-0.5 rounded">E:\projetos\ivan-helpdesk\deploy\desktop\</code><br>
                Repositório: <a href="https://github.com/JIvanAV/Helpdesk" class="text-blue-600 hover:underline" target="_blank">github.com/JIvanAV/Helpdesk</a>
            </p>
        </div>
    </body>
    </html>
    """


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "service": "ivan-helpdesk-api",
        "version": "0.1.0-dev",
        "day": 1,
        "message": "Database layer ready. API endpoints coming Days 2-3."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)