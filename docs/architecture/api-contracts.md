# Contratos de API e segurança da demonstração

Prefixo de negócio: `/api/v1`. A API também mantém `/health`, `/health/live`, `/health/ready`, `/docs` e `/openapi.json`.

| Método / caminho | Acesso | Resultado |
| --- | --- | --- |
| GET /api/v1/health | Público | 200 `{"status":"ok"}` se o banco responde; 503 se indisponível |
| GET /api/v1/customers | Público, somente perfis fictícios | Lista de id, nome, e-mail fictício e perfil, sem senha/conta/saldo |
| POST /api/v1/auth/login | E-mail e senha de desenvolvimento no JSON | Token Bearer, expiração, cliente e suas contas; 401 para credenciais inválidas |
| GET /api/v1/auth/me | Bearer | Cliente da sessão |
| POST /api/v1/auth/logout | Bearer | 204 e revogação persistida |
| GET /api/v1/accounts | Bearer | Somente as contas do cliente da sessão |
| GET /api/v1/accounts/{id} | Bearer e propriedade da conta | Conta ou 404 indistinguível de conta alheia |
| GET /api/v1/accounts/{id}/balance | Bearer e propriedade | `account_id`, `currency: BRL`, `balance` string decimal |
| GET /api/v1/accounts/{id}/ledger | Bearer e propriedade | Lançamentos confirmados; `limit` 1–100 (padrão 50), `offset` ≥ 0 |

## Contrato monetário

`"balance": "2947.53"`, `"amount": "0.29"` e saldo zero `"0.00"`. O sinal de saldo pode ser negativo. O ledger armazena montantes positivos e direção `credit`/`debit`; o saldo é a soma algébrica em PostgreSQL NUMERIC(18,2), retornada como Decimal no Python. Respostas serializam duas casas decimais. Não armazenar ou somar valores financeiros em float. O frontend formata a string decimal sem convertê-la em Number. As fixtures antigas continuam usando centavos inteiros somente nos cenários isolados.

As TASK-012–014 conectam receitas, despesas e Pix simulados ao ledger com atomicidade, bloqueio de conta e idempotência. O cenário visual antigo permanece separado em `/local-movement`.

## Erros e OpenAPI

Erros usam `{"error":{"code":"...","message":"...","details":[]},"request_id":"..."}`. Validações incluem somente nome e código do campo, nunca input, senha ou contexto interno. 401 invalida a sessão no cliente (exceto erro de login); 404 protege contas inexistentes/alheias; 422 indica validação; 503 indisponibilidade do banco; 500 erro inesperado sem diagnóstico privado. OpenAPI documenta esses modelos e o esquema HTTP Bearer.

O cliente Axios usa timeout de 10 segundos, cancelamento e tratamento separado de rede, timeout, validação e servidor. Nenhuma falha se transforma em saldo zero ou fixture de sucesso. Hooks vinculam respostas à conta/versão da consulta e descartam requisições canceladas.

## Sessão e limitações

Senha: PBKDF2-SHA256 com salt exclusivo e 600.000 iterações. Token: 32 bytes aleatórios em base64url, somente hash SHA-256 persistido. Expiração e revogação são verificadas em cada consulta protegida. O app mantém o token apenas na memória e o descarta ao expirar; não há refresh token nem persistência de login nesta etapa.

A senha de desenvolvimento compartilhada entre perfis é exclusivamente para demonstração com dados fictícios e fica no `.env` local ignorado pelo Git. A listagem de perfis é pública para o seletor. Este ambiente local não oferece identidade de produção, TLS ou limitação de tentativas de login; não o exponha à internet.

## Persistência

`0001_baseline` foi preservada; `0002_accounts_auth_ledger` adiciona customers, accounts, ledger_entries e auth_sessions, com índices, chaves estrangeiras e constraints. O seed é um processo separado após migrações e não substitui senhas, contas ou créditos existentes. Alterar DEMO_PASSWORD depois do primeiro seed não altera hashes já persistidos; rotação de credenciais requer procedimento próprio posterior.


## TASK-011 a TASK-020

Todos os caminhos abaixo usam `/api/v1`. Rotas de conta exigem Bearer e propriedade; conta alheia recebe 404.

| Método / caminho | Contrato |
| --- | --- |
| GET /customers?profile=&search=&limit=50&offset=0 | Seletor público fictício, paginado, seis perfis. Limite 1–100. |
| GET /categories | Catálogo com id e nome; toda transação possui FK válida. |
| GET /accounts/{id}/transactions | `{items,next_cursor,total}`; `limit` 1–100, cursor opaco; filtros `date_from`, `date_to`, `category_id`, `direction`, `search`. Ordem por data e UUID decrescentes. Snapshot exclui inserções posteriores à primeira página. Reiniciar paginação ao alterar filtros. |
| POST /accounts/{id}/credits | Receita simulada persistida. |
| POST /accounts/{id}/debits | Despesa simulada, sem cheque especial. |
| POST /pix/simulate | Mesmo corpo de movimentação, mais `account_id` e `recipient` fictício obrigatório; débito sem transferência externa. |
| PATCH /accounts/{id}/transactions/{tx}/category | `{category_id}`; altera somente categoria, sem efeito financeiro. |
| GET /accounts/{id}/scenario | Relógio persistido, seed/versão, saldo confirmado e eventos pendentes com saldo agendado. |
| POST /accounts/{id}/scenario/advance | `{target_date: "AAAA-MM-DD"}`; 0–366 dias por chamada, sem regressão; retorna `processed_count`. |
| POST /accounts/{id}/scenario/events | `kind`: salary_delay, extra_purchase ou extra_income; `scheduled_on`, `idempotency_key` UUID, `amount` decimal e `delay_days` 1–60. Data futura em até 366 dias; atraso exige salário pendente na data informada. |
| GET /accounts/{id}/data-summary | Quantidade, datas extremas, saldo e `fictitious: true`. |
| GET /accounts/{id}/recurrences | Séries mensais detectadas, valor típico, próxima data, ocorrências, regularidade e método; somente realizados até o relógio do cenário. |

Corpo de crédito/débito: `amount` como string positiva com duas casas (até 16 dígitos inteiros), `description` 1–120 caracteres, `category_id` opcional, `idempotency_key` UUID. Padrões: income para crédito, other para despesa e pix para Pix. Resposta: `{transaction,balance,simulated:true}`; valores monetários são strings. O comprovante identifica sempre a mesma transação; `balance` reflete o saldo consultado na resposta, inclusive em retry. A chave é isolada por conta e compartilhada entre tipos de operação: repetição idêntica reutiliza o lançamento; payload diferente retorna 409. O mobile conserva o payload/chave após falha ambígua. Saldo insuficiente retorna 409; validação/categoria inválida retorna 422, sem lançamento.

Escritas bloqueiam a linha da conta antes de verificar referência e saldo e fazem um único commit. Eventos sintéticos futuros ficam fora do ledger e do detector; avanço materializa todos os eventos elegíveis e o relógio em um único commit. Apenas eventos sintéticos podem resultar em saldo negativo, para explorar cenários de risco. O saldo agendado considera somente eventos conhecidos e não é previsão treinada. Atrasos alteram somente a agenda pendente, mantendo a data original e o histórico realizado.

Migração `0003_transactions_scenarios`: catálogo/backfill, metadados no ledger, perfis compartilháveis, cenários, eventos e ações idempotentes. `Transaction` reutiliza `ledger_entries`, evitando duplicação de saldo. Downgrade com múltiplos clientes no mesmo perfil é recusado para impedir perda de dados; em banco limpo ou com os três perfis anteriores, o ciclo é reversível.

Detector `monthly-heuristic-v1`: mínimo três ocorrências, meses consecutivos, dia típico ±3 dias e valor mediano ±10%; exige regularidade mínima de 75% nas três dimensões. Não é modelo treinado; `confidence_kind=observed_regularity` não é probabilidade calibrada. Precision e recall medidos e limitações constam no status de implementação.

## Previsão e séries — TASK-021 a 030

Todas as rotas abaixo exigem sessão e propriedade da conta, com prefixo `/api/v1/accounts/{account_id}`:

| Método / rota | Contrato |
| --- | --- |
| GET `/daily-series` | `base_date`, `series`: data, income/expense como strings, referências do ledger; lacunas zeradas e dados posteriores ao corte excluídos. |
| POST `/forecasts` | Corpo `{ "horizon": 7, "method": "hybrid" }`; horizonte 7/15/30; métodos hybrid/constant/moving_average/seasonal. Cria snapshot. |
| GET `/forecasts` | Até 100 snapshots, mais recentes primeiro. |
| GET `/forecasts/{run_id}` | Snapshot imutável pertencente à conta, ou 404. |

`ForecastRun` inclui UUID, data-base, horizonte, método, model_version, dataset_version, seed, points, risk e estimate_notice. Cada ponto contém data, receitas, despesas fixas/variáveis/totais, saldo e eventos mensais previstos. Valores são strings decimais. Risco é a primeira data com saldo negativo e seu valor, ou null; não é probabilidade calibrada. Os tipos compartilhados ficam em `mobile/src/features/forecasting/contracts.ts`.

A migração `0004_forecasts` adiciona disponibilidade e vínculo de estorno ao ledger e cria runs/pontos com NUMERIC(18,2). Triggers PostgreSQL rejeitam UPDATE/DELETE nos snapshots. O payload JSON preserva detalhes e os pontos guardam os valores financeiros em NUMERIC. O motor não lê eventos agendados futuros.

## Avaliação, experiência e alertas — TASK-041 a 058

Prefixo autenticado `/api/v1/accounts/{account_id}`; conta alheia retorna404:

| Método/rota | Comportamento |
| --- | --- |
| POST/GET `/experiments` | Datas train_end/validation_end/final_end e seed42; retorna ID, experiment_version, dataset, modelo/artefato, hiperparâmetros, seleção e métricas. Repetição exata recupera registro; nova seleção no mesmo dataset final recebe409. |
| GET `/evaluation/reports` | `format=json|csv|html`, filtros `model`, `horizon`, `profile`, `partition`; HTML tem controles de filtro. O perfil não amplia autorização para contas de terceiros. |
| GET `/forecasts/latest` | `{forecast, current_balance, current_date, stale, future_balance, income, risk}`; filtro opcional horizon7/15/30. Sem snapshot: forecast=null e stale=true. |
| GET `/forecasts/{run_id}/series` | Pontos por data com predicted_balance/expense e observed_balance/expense; observado futuro=null; desvio em reais/percentual e elegibilidade condicionada a déficit atual não obsoleto. |
| POST `/forecasts/simulate` | `{amount:"10.00",horizon:30}` → before/after/amount/hypothetical/persisted=false; nenhum ledger/run/alerta inserido. |
| GET/PUT `/alert-rules` | `{enabled:true,critical_days:3}`, janela0..30. |
| GET `/alerts` | Até100 alertas da conta; UUID, run_id, severidade, explicação, data/valor de déficit, recomendação e leitura. |
| GET/PATCH `/alerts/{alert_id}` | Detalhe e marcação `{"read":true}` idempotente. |
| POST `/forecast-refreshes/retry` | Reprocessa até20 eventos pendentes/failed, retornando status e correlation_id. Não refaz operação financeira. |

`GET /api/v1/observability` exige sessão; expõe contadores locais ao processo, sem detalhes bancários. Respostas HTTP trazem X-Request-ID/X-Correlation-ID; logs JSON não incluem corpo, senha ou token. Não existe coletor externo/garantia de retenção de logs implantada.

Créditos/débitos/Pix mantêm contratos anteriores e acrescentam `forecast_id`, `previous_forecast_id`, `forecast_status` e `correlation_id` ao receipt. Ledger e evento de recálculo são confirmados antes da inferência. Uma falha do modelo mantém status failed recuperável; não desfaz a transação. Novos runs também podem gerar alertas deduplicados por conta/data. ForecastRun aceita campos opcionais experiment_id/experiment_version, mas previsões de treino individual não são vinculadas artificialmente a um experimento diferente; ID/version aparecem no relatório do experimento efetivamente executado.

Migrações `0005_evaluation` (experimentos imutáveis) e `0006_alerts_refresh` (regras, alertas, eventos duráveis) seguem `0004_forecasts`. Hiperparâmetros/artefatos ML são JSON; dinheiro persiste NUMERIC e trafega como string decimal. Nenhuma API de dispositivo/push remoto foi necessária para notificações locais.
