# Repositório: Ivan Helpdesk

## Qualidade do Código e CI
Este projeto utiliza GitHub Actions para garantir que cada commit no branch `main` ou PR mantenha os testes de domínio e integração passando.

Workflow configurado: `.github/workflows/ci.yml`
- Disparado em: `push`, `pull_request`
- Ambiente: `ubuntu-latest`
- Passos: Setup Python 3.11 -> Instala dependências -> Executa `pytest deploy/desktop/backend/test_api_frontend.py`

Status da integração: Verifique a aba "Actions" no repositório GitHub.
