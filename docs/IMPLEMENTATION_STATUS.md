# Status de implementação — Sprints 1 e 2

Validação executada em 23/10/2026. PO, DEV e QA aplicados sequencialmente conforme `agents/personas/{po,dev,qa}.md`. Escopo: TASK-001 a TASK-010, exclusivamente dados fictícios. Entradas, saídas, dependências e casos-limite estão em [sprints-01-02.md](requirements/sprints-01-02.md).

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
