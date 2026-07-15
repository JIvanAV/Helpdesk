# Histórico de alterações dos chamados

O Ivan Helpdesk agora registra eventos de auditoria para mudanças importantes em cada chamado.

## O que fica registrado

- alteração de status;
- alteração de prioridade;
- alteração de categoria ou origem;
- mudança de técnico responsável;
- nova anotação de resolução;
- novo comentário interno.

## Endpoint

```http
GET /tickets/{ticket_id}/audit
```

Resposta resumida:

```json
[
  {
    "id": 1,
    "ticket_id": 42,
    "event_type": "field_change",
    "description": "Status alterado de 'aberto' para 'em_andamento'.",
    "technician": "Ivan Suporte",
    "created_at": "2026-07-15T18:30:00"
  }
]
```

## Uso no demo

Na interface local, cada card de chamado exibe a seção **Histórico de alterações do chamado** quando já existem eventos registrados. Isso ajuda a demonstrar rastreabilidade, responsabilidade técnica e manutenção profissional do atendimento.

## Próximos passos possíveis

- filtros por técnico no histórico;
- exportação do histórico em CSV;
- tela administrativa de auditoria;
- eventos de criação e exclusão lógica;
- integração futura com métricas de produtividade.
