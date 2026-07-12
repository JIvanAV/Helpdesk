# Revisão de qualidade de código

Este documento registra a direção de refatoração leve do Ivan Helpdesk: manter o projeto simples, legível e fácil de explicar em uma entrevista técnica.

## Objetivo

Ajustar o código para parecer mais próximo de uma manutenção manual e consciente, sem criar arquitetura desnecessária para um projeto de portfólio.

## Decisões aplicadas

- Preservar o comportamento existente antes de qualquer alteração visual ou estrutural.
- Preferir nomes explícitos em português quando o conceito aparece para o usuário final, como `ordem` na listagem de chamados.
- Isolar pequenos detalhes repetidos em helpers simples, como formatação de horário e escolha do nome do técnico.
- Centralizar rótulos e classes visuais repetidas da SPA em mapas pequenos (`LABELS` e `BADGES`).
- Evitar comentários artificiais; manter comentários apenas quando explicam uma regra de negócio ou intenção de manutenção.

## Pontos revisados

| Área | Ajuste | Motivo |
|---|---|---|
| API FastAPI | Parâmetro interno de ordenação separado do alias público `sort` | Deixa claro que o contrato HTTP continua igual, mas o código interno fica mais legível |
| Service layer | Helpers para timestamp e técnico responsável | Reduz repetição e evita fallback inconsistente em comentários/resoluções |
| Frontend SPA | Mapas de labels e badges | Facilita futuras alterações de texto/estilo sem procurar vários objetos inline |
| Testes | Testes direcionados e smoke da SPA após cada alteração | Garante que a refatoração não mudou comportamento |

## Regras para próximas evoluções

1. Uma melhoria por commit sempre que possível.
2. Refatorar somente trechos próximos da funcionalidade alterada.
3. Não trocar nomes públicos da API sem compatibilidade ou teste.
4. Não transformar a SPA simples em framework pesado antes de necessidade real.
5. Rodar testes do backend e smoke da interface antes de fazer push.
