# Status de implementação — AgiPrevê

Atualização mais recente: TASK-011–020, com aceite automatizado registrado ao final deste documento.

Validação inicial executada em 23/10/2026. PO, DEV e QA aplicados sequencialmente conforme `agents/personas/{po,dev,qa}.md`. Escopo: TASK-001 a TASK-010, exclusivamente dados fictícios. Entradas, saídas, dependências e casos-limite estão em [sprints-01-02.md](requirements/sprints-01-02.md).

## Resultado por task

APROVADA indica aceite coberto pelas evidências abaixo; não significa homologação visual Android/iOS. BLOQUEADA indica critério de aceite ainda não verificado.

| Task | Implementação e evidência executada | Status |
| --- | --- | --- |
| 001 | Monorepo modular, README, Uvicorn iniciado no Compose; Expo/Metro iniciou na porta 18082; bundle web gerado (904 módulos). DevTools apresentou erro auxiliar de sandbox, sem impedir Metro. | APROVADA |
| 002 | Build/up isolado, PostgreSQL e API saudáveis, migração/seed concluídos; registro continuou existente após reinício do banco. | APROVADA |
| 003 | Exemplos documentados; testes de URL, banco, CORS, senha e duração; `.env` locais ignorados pelo Git. | APROVADA |
| 004 | Upgrade/downgrade/upgrade em schema PostgreSQL exclusivo, inspeção de NUMERIC(18,2) e Decimal. | APROVADA |
| 005 | Axios e contratos; testes de rede, timeout, cancelamento, 422, 5xx, 401 e erros apresentados pelo card com retry. OpenAPI validado. | APROVADA |
| 006 | Build Python 3.12 com instalação das dependências; 26 testes com PostgreSQL; Ruff; npm ci seguido de typecheck, lint, testes puros e 20 testes Jest. | APROVADA |
| 007 | Quatro abas implementadas: Início, Extrato, Pix e AgiPrevê; Conta auxiliar. Health real e bundle passaram. Navegação visual entre abas e cartão conectado em execução não foram verificados. | BLOQUEADA |
| 008 | Clientes/contas/ledger/seed; integração comprova uma conta por perfil, saldo consistente e seed repetido sem duplicação. | APROVADA |
| 009 | Login, expiração, revogação/logout e autorização; testes comprovam 401 para sessão inválida e impedimento de acesso às contas/ledger/saldo de terceiros. | APROVADA |
| 010 | Saldo calculado por créditos menos débitos; PostgreSQL comprova precisão e zero; componente comprova loading, erro/retry, vazio e valor oculto sem fixture de fallback. | APROVADA |

## Comandos e resultados

Executados na raiz, salvo indicação:

| Comando | Resultado |
| --- | --- |
| `docker compose config --quiet` | Passou. |
| `docker compose -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests` | Instalação Python 3.12 e 26 testes aprovados; nenhum skip. |
| `python3 scripts/verify_infrastructure.py` | PASS: startup, migrations, seed, health e persistência após restart. Projeto/volume temporários removidos pelo script. |
| `docker run --rm -v /home/mayara/Projetos/agiPreve/backend:/app agipreve-test-tests ruff check --no-cache .` | All checks passed após correção. |
| `docker run --rm -v /home/mayara/Projetos/agiPreve/backend:/app agipreve-test-tests ruff format --no-cache --check .` | 43 arquivos formatados. |
| `docker compose -f compose.test.yaml run --rm -v /home/mayara/Projetos/agiPreve/backend:/app tests pytest -p no:cacheprovider` | Revalidação final: 26 passaram, 1 warning de depreciação Starlette/httpx, sem skips. |
| `npm install --fetch-retries=0 --fetch-timeout=20000` em mobile | Dependências resolvidas; lockfile atualizado. Auditoria online indicou 52 vulnerabilidades transitivas (3 moderadas e 49 altas); não houve atualização automática com quebra de versões. |
| `npm ci --offline --ignore-scripts` em mobile | Instalação limpa: 1104 pacotes. Não houve auditoria online neste comando; sua mensagem de zero vulnerabilidades não substitui a auditoria anterior. |
| `npm run check` em mobile após npm ci | TypeScript e lint sem erros; arquivo de regressões puras passou; 3 suítes Jest, 20 testes passaram. |
| `npm exec -- expo export --platform web --output-dir /tmp/agipreve-web-acceptance` em mobile | Bundle web gerado: 904 módulos. |
| `CI=1 npm start -- --offline --port 18082` em mobile | Metro iniciou e aguardou em localhost:18082. DevTools auxiliar falhou por configuração do sandbox; encerrado após coleta. |
| `git diff --check` e `git check-ignore .env backend/.env mobile/.env` | Sem erros de whitespace; três arquivos locais ignorados. |

## Defeitos corrigidos e revalidação

- Ruff identificou imports e formatação fora do padrão: corrigidos e checagem repetida com sucesso.
- Jest dependia de EXPO_PUBLIC_API_URL do ambiente: criado setup exclusivo de testes, com endpoint fictício; configuração de produção continua obrigatória.
- Duas asserções do card esperavam texto parcial em matcher exato: ajustadas ao conteúdo completo; 20 testes passaram.
- Axios produzia avisos de import: substituído por imports nomeados; lint passou.
- Testes backend tentavam ler `.env` local montado com permissão restrita: fixture passou a isolar configuração do arquivo de desenvolvimento; reexecução final com 26 testes aprovados.
- Alembic sem path_separator: configurado `os`; warning eliminado na revalidação final.
- Documentação antiga de três abas e ausência de endpoints foi atualizada com o estado das Sprints 1 e 2.

## Endpoints e migrações

Nenhum novo endpoint ou esquema de banco foi necessário nesta rodada de correções. Foram preservados `/health`, `/health/live`, `/health/ready`, `/api/v1/health`, `/api/v1/customers`, `/api/v1/auth/{login,me,logout}`, `/api/v1/accounts`, `/api/v1/accounts/{id}`, `/api/v1/accounts/{id}/balance` e `/api/v1/accounts/{id}/ledger`. Detalhes em [api-contracts.md](architecture/api-contracts.md).

Migrações existentes: `0001_baseline` e `0002_accounts_auth_ledger`; a segunda recebeu somente formatação/imports. O ciclo de migração foi validado em schema exclusivo de teste, sem downgrade no banco de desenvolvimento.

## Arquivos desta rodada

Alterações anteriores do workspace foram preservadas. Nesta rodada foram corrigidos:

```text
README.md
docs/
  IMPLEMENTATION_STATUS.md (criado)
  requirements/mvp-scope.md
  architecture/project-structure.md
  guides/local-development.md
backend/
  alembic.ini
  app/ (imports e formatação nos arquivos apontados pelo Ruff)
  migrations/ (imports e formatação)
  tests/ (formatação e conftest.py com isolamento do ambiente)
mobile/
  package-lock.json
  jest.config.cjs
  tests/setup.cjs (criado)
  __tests__/BalanceCard.test.tsx
  src/services/http.ts
  src/app/account.tsx
```

Não foram criados Markdown temporários na raiz, diretórios permanentes de testes documentais ou cópias de personas. Caminhos documentais foram inspecionados; personas permanecem em `agents/personas/`.

## Pendências e próximo passo

- TASK-007: executar navegação visual entre quatro abas e verificar cartão de conectividade no aplicativo. Não verificado por encerramento das validações solicitado pelo usuário; não há aprovação visual Android/iOS.
- Experimento adicional de UI via Playwright não foi concluído: instalação do navegador sem acesso ao cache e projeto Docker adicional com conflito na porta 5432; recursos Docker exclusivos desse experimento removidos. Não afeta o teste isolado de infraestrutura já aprovado.
- Revisar vulnerabilidades transitivas em tarefa própria, mantendo a compatibilidade Expo; nenhuma correção com `--force` foi aplicada.
- Disponibilidade de 99%, carga, métricas preditivas e integrações bancárias reais não foram validadas nem fazem parte desta entrega.
- Próxima atividade: fechar o aceite visual da TASK-007. Demais implementações posteriores não foram iniciadas. Pix persistido, previsão treinada e push permanecem fora do escopo.

## Atualização — TASK-011 a TASK-020 (23/10/2026)

**Status do lote: APROVADA no aceite automatizado.** As dez tasks foram implementadas no frontend/backend. PO, DEV e QA aplicados sequencialmente, sem subagentes. Entradas, saídas, políticas, dependências e casos-limite em [sprints-02-03.md](requirements/sprints-02-03.md). Homologação visual Android/iOS continua **não verificada**; não altera retrospectivamente a pendência da TASK-007.

### Evidências por task

| Task | Implementação e aceite executado | Status |
| --- | --- | --- |
| 011 | Transaction reutiliza o ledger; extrato por cursor com período, direção, categoria e descrição. Teste percorreu todas as páginas com datas empatadas, verificou ordem, IDs únicos, snapshot contra inserção posterior, filtros e parâmetros inválidos. | APROVADA |
| 012 | Formulário/revisão/comprovante pela API; crédito atômico altera saldo uma vez. Testes verificaram retry, conflito de payload e valor inválido sem lançamento. Extrato lê o mesmo ledger. | APROVADA |
| 013 | Despesa com categorias; sem cheque especial. Testes comprovaram débito único, insuficiência sem alteração e duas saídas concorrentes com somente uma aprovada quando não há saldo para ambas. | APROVADA |
| 014 | Pix com favorecido fictício, revisão e comprovante persistido. Backend verificou idempotência; teste de rollback após flush comprovou ausência de débito parcial. RNTL verificou confirmação, erro sem falso sucesso, retry com mesma chave e bloqueio de segundo envio em andamento. | APROVADA |
| 015 | Catálogo com FK, classificação padrão, backfill de linhas antigas e edição no extrato. Testes verificaram catálogo válido, alteração sem efeito no saldo, categoria inválida e proteção contra conta/transação alheia. | APROVADA |
| 016 | Cenário por conta, data monotônica e agenda separada. Avançar materializou eventos uma vez; retry processou zero eventos. Histórico anterior preservado; regressão de data recusada; rollback preservou relógio e agenda. | APROVADA |
| 017 | Gerador parametrizado, seis perfis, IDs/dados financeiros determinísticos. Testes geraram 1000 clientes, verificaram perfis distintos, mesma seed/dados, seeds diferentes e reexecução sem duplicação. Outros seis clientes gerados com senha habilitada foram validados por login/seletor e filtro de perfil. | APROVADA |
| 018 | Gerados e inseridos em PostgreSQL 158000 lançamentos realizados em 365 dias/12 meses, 1000 contas e 36000 eventos futuros separados. Saldo de cada uma das 1000 contas reconciliado com a origem determinística; e-mails somente @demo.local; nenhum lançamento futuro no histórico. | APROVADA |
| 019 | Área dev e API de atraso salarial, compra extraordinária e receita eventual. Testes verificaram data do salário deslocada uma vez, futuro agendado alterado em +15.00 por receita de 25.00 e compra de 10.00, saldo confirmado intacto até avanço e mesmo efeito após retry. | APROVADA |
| 020 | Heurística mensal com tolerância de dia/valor, regularidade explícita e próxima data; exibida no AgiPrevê e área dev. Avaliação em 18 cenários rotulados, três seeds de avaliação e seis perfis: TP=49, FP=0, FN=5, precision=1.0 e recall=0.9074074074. Testes de jitter, ruído, histórico insuficiente e exclusão de futuro passaram. | APROVADA |

### Comandos executados e resultados

- `docker compose -f compose.test.yaml run --rm --no-deps -v /home/mayara/Projetos/agiPreve/backend:/app tests pytest tests/test_api_errors.py tests/test_banking_integration.py tests/test_config.py tests/test_health.py tests/test_migrations_integration.py tests/test_money_type.py tests/test_security_stdlib.py tests/test_recurrences.py tests/test_transactions_simulation.py -p no:cacheprovider -s`: **36 passaram**, nenhum skip, 37.85s, um warning de depreciação Starlette/httpx. Banco descartável `_test`, schemas exclusivos; sem alteração no banco de desenvolvimento.
- `ruff check --no-cache` nos arquivos deste lote (via `docker run` com a imagem `agipreve-test-tests`): passou; imports corrigidos com `--fix` antes da revalidação.
- `ruff format --no-cache --check` no mesmo escopo: **20 arquivos formatados**.
- `npm run check`, em `mobile/`: TypeScript e lint passaram; teste de regressões puras passou; **5 suítes Jest e 33 testes passaram**.
- `npm exec -- expo export --platform web --output-dir /tmp/agipreve-sprint3-web`, em `mobile/`: bundle gerado, **912 módulos**. Não substitui execução visual nativa.
- `git diff --check`: passou. Organização Markdown inspecionada: somente `docs/requirements/sprints-02-03.md` foi criado; status e guias existentes atualizados, sem novos documentos dispersos na raiz ou diretório permanente de documentação de testes.

Os testes de PostgreSQL foram iniciados com Compose antes da regressão. O serviço descartável foi mantido disponível porque outra implementação está usando o mesmo workspace; nenhum volume de desenvolvimento foi removido. Tentativas de npm na raiz falharam por ausência de package.json e foram repetidas corretamente em `mobile/`.

### Defeitos corrigidos pelo ciclo DEV/QA

- Comparar intervalos mensais somente por dias rejeitava fevereiro com variação de data permitida. Corrigido para sucessão de meses com tolerância no dia típico; testes de borda e métricas reexecutados.
- Lint React apontou ref usada na renderização e efeitos com atualização síncrona. Payload de revisão passou a estado imutável, e carregamentos usam respostas assíncronas; typecheck/lint e componentes revalidados.
- Um teste novo de rollback tinha imports ausentes. Corrigido e reexecutado isoladamente; depois a regressão final completa de 36 testes passou.
- Filtros do seletor descartam respostas antigas; mudanças de página/perfil limpam seleção. Mudanças bancárias invalidam consultas de saldo, extrato e recorrências sem fallback para cenários.
- Falhas definitivas de validação no agendamento permitem corrigir campos; falhas ambíguas preservam a chave para retry.

### Endpoints e migração

Novos endpoints em `/api/v1`:

- `GET /categories`.
- `GET /accounts/{id}/transactions`.
- `POST /accounts/{id}/credits` e `POST /accounts/{id}/debits`.
- `POST /pix/simulate`.
- `PATCH /accounts/{id}/transactions/{tx}/category`.
- `GET /accounts/{id}/scenario`.
- `POST /accounts/{id}/scenario/advance` e `POST /accounts/{id}/scenario/events`.
- `GET /accounts/{id}/data-summary` e `GET /accounts/{id}/recurrences`.

`GET /customers` ganhou paginação e filtros compatíveis com o contrato anterior de lista. Rotas antigas de saldo/ledger/auth foram preservadas e seus testes passaram.

Migração **0003_transactions_scenarios**: categorias e backfill, metadados no ledger, perfis compartilháveis, cenários, eventos pendentes e chaves de ações. Testados upgrade/downgrade/upgrade em schema limpo e preservação de IDs/valores após upgrade de dados antigos. Não foi aplicado downgrade ou gerador no banco de desenvolvimento. Contratos e limites em [api-contracts.md](architecture/api-contracts.md); comando de geração no [guia local](guides/local-development.md).

### Árvore criada ou modificada neste lote

```text
README.md
backend/
  app/api/router.py
  app/seed.py
  app/modules/banking/
    models/__init__.py
    routers/__init__.py
    transactions.py (novo)
    transaction_router.py (novo)
  app/modules/simulation/ (novo)
    __init__.py
    models.py
    services.py
    generator.py
  app/modules/forecasting/recurrences.py (novo)
  migrations/env.py
  migrations/versions/0003_transactions_scenarios.py (nova)
  tests/test_migrations_integration.py
  tests/test_transactions_simulation.py (novo)
  tests/test_recurrences.py (novo)
mobile/
  src/app/{index,movement,account,_layout}.tsx
  src/app/{dev-scenario,local-movement}.tsx (novos)
  src/app/(tabs)/{index,statement,pix,agipreve}.tsx
  src/auth/AuthProvider.tsx
  src/demo/DemoProvider.tsx
  src/features/banking/{contracts,useBalance,useLedger}.ts
  src/features/banking/{inputs,refresh,useCategories}.ts (novos)
  src/features/banking/components/RecurrencesCard.tsx (novo)
  __tests__/{Movement.test.tsx,banking-inputs.test.ts} (novos)
docs/
  IMPLEMENTATION_STATUS.md
  requirements/{mvp-scope.md,sprints-02-03.md (novo)}
  architecture/{api-contracts.md,project-structure.md}
  guides/local-development.md
```

### Limites, riscos e próxima frente

- **Não verificado:** interação visual Android/iOS e usabilidade em dispositivo. Os critérios financeiros, de geração e de componentes foram executados; não houve homologação nativa.
- Métricas limitadas aos 18 cenários sintéticos rotulados; cinco recorrências de renda variável/sazonal não foram detectadas. Não são resultados em dados bancários reais nem evidência de modelo treinado/calibrado. Disponibilidade, carga concorrente de 1000 usuários e métricas preditivas não foram medidas.
- O gerador completo não é executado automaticamente no startup. A prova com 1000 clientes usou login desabilitado nesse conjunto para evitar custo de 1000 hashes nos testes; login foi testado separadamente com seis clientes gerados, um de cada perfil. O comando administrativo real habilita as senhas fictícias com salts individuais.
- Registros já gerados são preservados em reexecução; nova seed produz outro conjunto. Downgrade com vários clientes no mesmo perfil é recusado para impedir perda de dados.
- Durante a execução surgiram arquivos de previsão e migração `0004_forecasts` de trabalho paralelo. Foram preservados. Uma checagem ampla inicial aplicou somente imports/formatação em arquivos Python presentes naquele momento; as verificações Ruff posteriores foram limitadas a este lote. A regressão final passou no estado disponível, mas não constitui aprovação das tarefas do trabalho paralelo. Um erro transitório em PersistedForecast apareceu e deixou de ocorrer na checagem final, sem implementação dessa funcionalidade por este lote.
- Próxima frente desbloqueada: consumir histórico e recorrências persistidos nas tarefas de previsão. Nenhuma funcionalidade além de TASK-011–020 foi iniciada por esta execução.

## TASK-021 a TASK-030 — dados e motor de previsão (23/10/2026)

**Status: APROVADA nos critérios automatizados do MVP.** Validação visual Android/iOS **não verificada**, sem dispositivo/emulador nesta execução. Aplicadas sequencialmente as personas PO, DEV e QA; alterações anteriores de TASK-001 a 020 preservadas. Não há aprovação de acurácia estatística, calibração ou desempenho p95.

### PO — requisitos, entradas e saídas

Refinamento em [sprints-03-04.md](requirements/sprints-03-04.md). Entradas: ledger fictício persistido, referência única, direção/valor Decimal, data econômica, disponibilidade, vínculo opcional de estorno e data do relógio simulado. Saídas: séries auditáveis, atributos causais, datasets particionados/versionados, baselines e previsões híbridas com metadados e pontos imutáveis. Dependências: transações, cenários, geração sintética e detecção mensal já presentes no workspace. Nenhuma API bancária real foi integrada.

### QA — evidência por critério

| Task | Status automatizado | Evidência executada |
| --- | --- | --- |
| 021 | APROVADA | Referência repetida conta uma vez; conflito rejeitado; lacunas zeradas; disponibilidade tardia excluída; estorno integral auditável, órfão/duplicado/inconsistente rejeitado. Integração com ledger persistido. |
| 022 | APROVADA | Lags 1/7, janela 7 dias, volatilidade e calendário calculados; recorrências/dias até receita verificados; acrescentar futuro não altera previsão; treino reconstrói histórico e padrões por origem. |
| 023 | APROVADA | Splits cronológicos com expurgo do horizonte; holdout separado; limites e seed alteram versão; exportação executada em diretório temporário; import tardio não aparece no treino anterior à disponibilidade. |
| 024 | APROVADA | API autenticada em 7/15/30; respostas com data-base, data de geração, versão, série diária e strings decimais; 401/404/422 verificados. |
| 025 | APROVADA | Três baselines determinísticos nos três horizontes; laboratório gera HTML/JSON e calcula MAE sobre validação realizada; tentativa de ultrapassar limite de validação rejeitada. |
| 026 | APROVADA | Fixture de salário mensal projeta dia 5 e valor 1000.00; fixture de fim de mês projeta dia 30 de abril após janeiro/fevereiro/março. Calendário retornado pela API e renderizado no componente. |
| 027 | APROVADA | Aluguel no dia 8 por 300.00, evento único e grupo retirado da componente variável; recorrência estornada não reutilizada sem evidência mínima. |
| 028 | APROVADA | Boosting de árvores rasas realmente treinado, versão reprodutível, sem ID de cliente; inferência aceita vetor fora do treino e é não negativa. API com histórico sintético de um ano retorna versão treinada. Histórico insuficiente é identificado explicitamente. |
| 029 | APROVADA | Identidade diária com Decimal verificada para todos os métodos e horizontes 7/15/30, incluindo fluxo com estorno. |
| 030 | APROVADA | Após novo crédito, versão nova muda e snapshot antigo consultado permanece idêntico; listas e isolamento entre contas verificados; UPDATE e DELETE de runs/pontos rejeitados pelo PostgreSQL. |

O laboratório é um relatório HTML técnico gerado pelo módulo `laboratory`, separado da aplicação bancária. O app consome agregações sem nova UI de agregação, permite gerar previsão híbrida, ver curvas de saldo/despesa variável, calendário e versões. Os cenários locais anteriores continuam identificados e separados.

### Comandos e resultados

Executados em PostgreSQL descartável via `compose.test.yaml`, com schemas de teste exclusivos:

- Regressão backend: `docker compose -f compose.test.yaml run --rm -v /home/mayara/Projetos/agiPreve/backend:/app tests pytest -p no:cacheprovider -q` — **55 passaram em 46.44s**, nenhum skip no estado anterior aos dois últimos testes adicionados.
- Revalidação final afetada: `pytest -p no:cacheprovider tests/test_forecasting.py tests/test_forecasting_integration.py tests/test_migrations_integration.py -q`, no mesmo container/mount — **23 passaram em 11.01s**, nenhum skip. Inclui os dois testes finais de erro controlado e disponibilidade na exportação. Um warning de depreciação Starlette/httpx, sem falha.
- `ruff check --no-cache` e `ruff format --no-cache --check` no módulo forecasting, modelos bancários, router principal, env/revisão 0004 e três arquivos de testes afetados — **passaram; 15 arquivos formatados corretamente**.
- `npm run check`, em `mobile/`, reexecutado após a alteração final do contrato/UI — **TypeScript e lint passaram; regressões puras passaram; 6 suítes Jest, 35 testes passaram**. Dois testes novos verificam calendário/metadados da API e falha sem previsão inventada.
- `git diff --check` — passou. Inventário Markdown inspecionado: novo refinamento somente em `docs/requirements/`, sem novos Markdown na raiz, sem duplicação de personas ou diretório documental de testes.
- Migrações: upgrade/downgrade/upgrade e preservação do ledger executados pelos testes PostgreSQL. **Não aplicado ao banco de desenvolvimento**; requer `alembic upgrade head` antes de executar o app com estes endpoints.

Tentativa inicial pelo Compose foi interrompida com exit 137; a validação foi retomada em `compose run` e concluída acima. Python/pytest/Ruff não estavam instalados no venv local; usados os executáveis da imagem do projeto. Uma tentativa de `npm run check` na raiz falhou por ausência de package.json e foi repetida corretamente em `mobile/`.

### Defeitos tratados no ciclo DEV/QA

- Validação de NaN comparava o número antes de verificar finitude: ordem corrigida e teste negativo passou.
- Atributos de recorrência não estavam incluídos no retorno inicial: adicionados e valores verificados; classificação histórica reconstruída por origem para impedir uso de recorrências descobertas depois.
- Estornos de despesas precisavam permanecer junto da referência original na componente variável: seleção corrigida e regressão executada.
- Disponibilidade era descartada na exportação de partições: exportação com fontes agora recalcula os agregados no limite de cada partição, preserva observações com disponibilidade e inclui essas fontes na versão. Teste de importação tardia passou.
- TypeScript detectou estado possivelmente nulo no componente: guarda explícita corrigida; check completo passou.
- Históricos inconsistentes agora recebem 422 controlado em série/previsão, testado com estorno divergente persistido.

### Endpoints, migração e arquivos deste lote

Prefixo `/api/v1/accounts/{account_id}`: `GET /daily-series`, `POST /forecasts`, `GET /forecasts`, `GET /forecasts/{run_id}`. Contratos em [api-contracts.md](architecture/api-contracts.md).

Migração **0004_forecasts**: adiciona `available_on` e `reversal_of` ao ledger; backfill de disponibilidade econômica do histórico sintético existente; cria ForecastRun/ForecastPoint, NUMERIC(18,2), índices/unicidade por run/data e triggers append-only. Não cria endpoint bancário de estorno.

```text
backend/
  app/api/router.py
  app/modules/banking/models/__init__.py
  app/modules/forecasting/
    pipeline.py (novo)
    datasets.py (novo)
    engine.py (novo)
    laboratory.py (novo)
    models.py (novo)
    router.py (novo)
  migrations/env.py
  migrations/versions/0004_forecasts.py (nova)
  tests/test_forecasting.py (novo)
  tests/test_forecasting_integration.py (novo)
  tests/test_migrations_integration.py
mobile/
  src/app/(tabs)/agipreve.tsx
  src/features/forecasting/{contracts.ts,api.ts,PersistedForecast.tsx} (novos)
  __tests__/PersistedForecast.test.tsx (novo)
docs/
  requirements/sprints-03-04.md (novo)
  architecture/api-contracts.md
  guides/local-development.md
  IMPLEMENTATION_STATUS.md
```

### Pendências e limites

- **Não verificado:** visual/usabilidade nativa Android/iOS. Renderização funcional do componente testada em Jest, com HTTP/charts substituídos apenas nos testes; fluxo de backend usa PostgreSQL real.
- Incerteza é declarada não calibrada. Não há alegação de superioridade do boosting sobre baselines; não foram executados seleção estatística, experimento final de qualidade ou calibração, que ficam nas tarefas de avaliação.
- Em novos imports históricos tardios, preencher `available_on` no relógio simulado; ausência do campo mantém semântica histórica de disponibilidade na data econômica. Estornos parciais/encadeados não são suportados.
- Treino do MVP é determinístico por execução, sem dependências ML extras; persistem versões e previsões, não um registro externo de artefatos/model serving. Carga e p95 não medidos nesta entrega.
- Próxima frente desbloqueada: integração de reprevisão após movimentação e avaliação temporal/real × previsto nas tarefas subsequentes. Não iniciadas nesta execução.
