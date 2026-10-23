# AgiPrevê

Protótipo demonstrativo não oficial, exclusivamente com dados fictícios. React Native/Expo/TypeScript no mobile e monólito modular FastAPI/Python 3.12/PostgreSQL no backend. Não há integração com o Agibank.

## Ferramentas e bibliotecas necessárias

Instale no computador:

- **Node.js 22.13 ou superior** (Node 24 recomendado) e **npm**, para executar o app Expo.
- **Docker Engine e Docker Compose v2**, ou Docker Desktop com Compose, para executar API e PostgreSQL 17.
- Para celular: **Expo Go compatível com SDK 57** ou um development build. Para emulador Android, instale Android Studio e configure um dispositivo virtual. O iOS Simulator exige macOS e Xcode.
- **Python 3.12 ou 3.13 com venv**, somente se executar a API fora do Docker.

As bibliotecas são instaladas pelos manifestos do projeto; não é necessário instalar Expo ou React Native globalmente.

| Parte | Bibliotecas utilizadas | Instalação |
| --- | --- | --- |
| App | Expo 57, React 19, React Native, TypeScript e Expo Router | `npm ci` em `mobile/` |
| Interface e gráficos | React Native Web, SVG, Chart Kit, Gesture Handler, Reanimated, Worklets, Safe Area Context, Screens e Expo Linear Gradient | Incluídas em `npm ci` |
| Integrações do app | Axios, Expo Constants, Linking e Notifications | Incluídas em `npm ci` |
| Qualidade do app | ESLint, Jest, Jest Expo e Testing Library | Incluídas em `npm ci` |
| API e banco | FastAPI, Pydantic, Pydantic Settings, SQLAlchemy 2, Alembic, Psycopg e Uvicorn | Automática no build Docker; instalação local abaixo |
| Qualidade da API | Pytest, HTTPX e Ruff | Incluídas no build Docker e no extra Python `dev` |

As versões do app estão em [package.json](mobile/package.json) e no lockfile; os intervalos Python estão em [pyproject.toml](backend/pyproject.toml). Para adicionar uma biblioteca nativa posteriormente, use `npx expo install nome-da-biblioteca` dentro de `mobile/`, respeitando a compatibilidade do SDK.

## Iniciar API e banco

Pré-requisitos: Docker Engine/Compose e acesso ao Docker Hub/PyPI; Node.js 22.13+ e npm para o mobile.

Na raiz, copie os exemplos somente se os arquivos locais ainda não existirem:

```bash
cp -n .env.example .env
cp -n backend/.env.example backend/.env
cp -n mobile/.env.example mobile/.env
```

Substitua `POSTGRES_PASSWORD` na raiz e mantenha a `DATABASE_URL` do backend local coerente. Configure `DEMO_PASSWORD` com pelo menos 12 caracteres (senha fictícia, nunca pessoal). O Compose usa o `.env` da raiz; o backend fora do Docker usa `backend/.env`. Neste workspace os arquivos locais já existem e não devem ser sobrescritos.

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps -a
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
```

A inicialização aplica as migrações e executa o seed idempotente de três clientes/contas. `migrate` e `seed` devem terminar com código zero. A API depende deles e do PostgreSQL saudável. Acesse [OpenAPI](http://localhost:8000/docs). O volume `postgres_data` preserva os dados em reinícios; não use `down --volumes` no ambiente de desenvolvimento.

## Iniciar o mobile

```bash
cd mobile
npm ci
npx expo install --check
npm start
```

Configure `EXPO_PUBLIC_API_URL` em `mobile/.env`: Android Emulator usa `http://10.0.2.2:8000/api/v1`; dispositivo físico usa `http://IP_DO_COMPUTADOR:8000/api/v1`; web/iOS Simulator usa `http://localhost:8000/api/v1`. Reinicie o Metro após mudar o arquivo. Use `npm run android` para abrir no emulador existente, ou `npm run web` para a prévia no navegador.

Para abrir diretamente no navegador, execute em um terminal separado, com a API ativa:

```bash
cd mobile
npm run web -- --port 8081
```

Acesse [app web](http://localhost:8081). Para celular físico, execute `npm start` e escaneie o QR Code com Expo Go; computador e celular devem estar na mesma rede e a porta 8000 precisa estar acessível. `localhost` no celular aponta para o próprio celular, portanto use o IP de rede do computador na URL da API.

Se o login ou o saldo falhar, confira `/health/ready`, a URL em `mobile/.env` e `docker compose logs --tail=100 api migrate seed`. Se a porta 8081 estiver ocupada, encerre a instância anterior; usar outra porta na web também exige incluí-la em `CORS_ORIGINS` no `.env` da raiz e recriar a API com `docker compose up -d api`.

Para encerrar o app, pressione `Ctrl+C` no terminal do Expo. Para encerrar API e banco preservando os dados:

```bash
docker compose down
```

Escolha um dos perfis fictícios retornados pela API e toque em **Entrar no protótipo**, sem informar senha. `DEMO_PASSWORD` permanece apenas para o seed e clientes antigos; não é necessária na interface. A sessão Bearer expira e o logout a revoga no servidor. O saldo confirmado é lido da API; os cenários/Pix visuais anteriores ficam explicitamente separados do ledger persistido.

A navegação solicitada na TASK-007 é **Início, Extrato, Pix e AgiPrevê**. A Conta permanece acessível pelo Início. O Laboratório não faz parte das abas.

## Backend local sem container

```bash
docker compose up -d db
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Qualidade e aceite

```bash
# Backend instalado localmente, dentro de backend/
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest -m 'not integration'

# Mobile, dentro de mobile/
npm run check
```

O lockfile inclui Axios/Jest. Para instalação limpa e reproduzível do mobile, use `npm ci`; execute `npm run check` em seguida.

Na raiz, os testes completos usam um PostgreSQL isolado e descartável, sem tocar no banco de desenvolvimento:

```bash
docker compose -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
docker compose -f compose.test.yaml down
python3 scripts/verify_infrastructure.py
```

O primeiro comando inclui upgrade/downgrade/upgrade e isolamento de sessões. O segundo teste usa um projeto Compose com nome aleatório, portas 18080/15432 e volume próprios para verificar persistência após reinício; remove somente os recursos desse projeto temporário. Se essas portas estiverem ocupadas, libere-as antes de executar.

Evidências, lacunas e status por tarefa: [IMPLEMENTATION_STATUS](docs/IMPLEMENTATION_STATUS.md). Requisitos refinados: [Sprints 1 e 2](docs/requirements/sprints-01-02.md). Arquitetura e contrato monetário: [estrutura](docs/architecture/project-structure.md).


## Transações e dados sintéticos

Receitas, despesas e Pix simulados são gravados pela API com idempotência e comprovante. O Extrato possui filtros e edição de categoria. Conta → Área dev permite avançar o cenário persistido e agendar eventos extraordinários. O AgiPrevê mostra recorrências detectadas por heurística, separadas das previsões visuais locais.

Gerador opcional, exclusivamente fictício:

```bash
docker compose exec api python -m app.modules.simulation.generator --seed 42 --count 1000
```

Procedimentos, limites e reprodução em [desenvolvimento local](docs/guides/local-development.md); contratos em [api-contracts.md](docs/architecture/api-contracts.md).

## Demonstração integrada, alertas e avaliação

Depois de `docker compose up --build -d`, conferir revisão `0006_alerts_refresh` com `docker compose exec api alembic current`. Para preparar um orçamento fictício com risco calculado, sem apagar contas existentes:

```bash
docker compose exec api python -m app.demo --seed 4241
```

Selecione `synthetic-4241-2@demo.local` e entre sem senha. O comando calcula uma despesa demonstrativa para deixar R$50,00, grava a operação e gera previsão/alerta reais do protótipo. Repetir a seed preserva dados; escolher outra seed para uma apresentação nova. Um Pix fictício de R$10,00 permite mostrar antes/depois. O app exibe saldo, previsões persistidas, real × previsto, central e simulação sem débito.

[Roteiro de 10 minutos](docs/guides/demo-walkthrough.md), [aceite GO/NO-GO](docs/MVP_ACCEPTANCE_REPORT.md) e [evidências por task](docs/IMPLEMENTATION_STATUS.md). O laboratório técnico oferece relatórios autenticados JSON/CSV/HTML por conta em `/api/v1/accounts/{id}/evaluation/reports`, com filtros; não é uma aba bancária. No OpenAPI, criar/recuperar experimentos em `/accounts/{id}/experiments`. Não colocar tokens em URLs ou documentação.

Notificações locais exigem ação de permissão e dispositivo Android/iOS. Push remoto não está habilitado. A homologação integral depende dos bloqueios explicitados no relatório; compilar web ou passar testes de componente não comprova entrega nativa.
