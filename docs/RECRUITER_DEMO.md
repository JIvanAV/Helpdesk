# Modo recrutador

O **Modo recrutador** prepara o Ivan Helpdesk para uma apresentação curta de portfólio, sem depender de cadastros manuais antes da entrevista.

## Objetivo

Criar um cenário limpo com chamados realistas de suporte técnico para demonstrar:

- triagem por prioridade e impacto operacional;
- atendimento por técnico responsável;
- acompanhamento de SLA;
- comentários de resolução e comentários internos;
- auditoria do chamado e exportação CSV.

## Como preparar a apresentação

1. Inicie o backend local:

   ```bash
   cd deploy/desktop/backend
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
   ```

2. Abra a interface:

   ```txt
   http://localhost:8001/
   ```

3. Clique em **Preparar demo** no painel **Modo recrutador**.

O botão chama `POST /demo/recruiter/reset`, recria os chamados de demonstração e recarrega painel, lista e métricas.

## Roteiro rápido de apresentação

| Etapa | O que mostrar | Mensagem para entrevista |
|---|---|---|
| 1 | Dashboard e resumo executivo | "Aqui eu consigo visualizar volume, SLA, criticidade e impacto operacional." |
| 2 | Chamado crítico de sistema financeiro | "Prioridade técnica e impacto operacional são tratados separadamente." |
| 3 | Botão **Assumir chamado** | "O atendimento registra o técnico responsável e muda o status para andamento." |
| 4 | Comentário técnico e comentário interno | "A solução pública e as notas internas ficam separadas para preservar o histórico." |
| 5 | Histórico de alterações e CSV | "As mudanças ficam auditáveis e podem ser exportadas para relatório." |

## Endpoint usado no demo

```http
POST /demo/recruiter/reset
```

Resposta resumida:

```json
{
  "total": 4,
  "page": 1,
  "page_size": 4,
  "tickets": []
}
```

## Observações

- O recurso é intencionalmente local e seguro para portfólio.
- Não usa senhas reais nem dados de clientes reais.
- O reset limpa os chamados atuais do banco local de demonstração antes de recriar o cenário.
