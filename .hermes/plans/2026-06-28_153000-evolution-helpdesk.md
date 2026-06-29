# Plano de Evolução do Ivan Helpdesk

> **Para Hermes:** Use a skill de `subagent-driven-development` para implementar este plano tarefa por tarefa.

**Objetivo:** Preparar o projeto para compartilhamento externo, implementar login via Google e limpar dados de teste mantendo um chamado tutorial.

**Arquitetura:** 
- A autenticação Google será integrada via FastAPI utilizando um middleware OAuth2 ou integração simples.
- Limpeza dos dados será feita via script de migração SQL/DB.
- Disponibilidade será via tunelamento (ngrok/Cloudflare Tunnel) ou documentação de deploy simples (Vercel/Render).

---

### Tarefa 1: Limpeza do Banco de Dados e Chamado Tutorial

**Objetivo:** Apagar todos os chamados atuais e inserir um chamado tutorial fixo.

**Passos:**
1. Escrever um script Python (`deploy/desktop/backend/reset_db.py`) que:
   - Limpa a tabela `tickets` no `helpdesk.db`.
   - Insere um chamado tutorial: "Tutorial: Como abrir chamados".
2. Executar o script.
3. Verificar com `sqlite3` ou script de teste.

### Tarefa 2: Implementação de Autenticação (Login Google)

**Objetivo:** Proteger o acesso via OAuth2 (Google).

**Passos:**
1. Instalar `authlib` e `httpx` no backend.
2. Criar `deploy/desktop/backend/auth.py`.
3. Integrar no `main.py` como dependência para a rota `/` (frontend).

### Tarefa 3: Documentação de Deploy (Compartilhamento)

**Objetivo:** Criar guia para o usuário compartilhar o app.

**Passos:**
1. Criar `DEPLOY_GUIDE.md` na raiz com instruções para:
   - Uso de `ngrok` para expor o localhost.
   - Alternativas como Render/Railway.
2. Adicionar link no `README.md`.

---

**Riscos:**
- A integração do Google OAuth2 requer configuração de console de desenvolvedor (precisaremos da ajuda do José para o Client ID/Secret).
- O backend atual é muito acoplado; pode precisar de refatoração para aceitar middleware de auth.

**Próximos passos:**
- Confirmar se o José aceita o uso de OAuth2 (precisará criar credenciais no Google).
- Iniciar pela limpeza do banco de dados.

---
Salvo em: `.hermes/plans/2026-06-28_153000-evolution-helpdesk.md`
