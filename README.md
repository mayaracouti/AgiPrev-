# AgiPrevê

Protótipo demonstrativo não oficial, exclusivamente com dados fictícios. React Native/Expo/TypeScript no mobile e monólito modular FastAPI/Python 3.12/PostgreSQL no backend. Não há integração com o Agibank.

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
curl --fail http://localhost:8000/health
```

A inicialização aplica as migrações e executa o seed idempotente de três clientes/contas. `migrate` e `seed` devem terminar com código zero. A API depende deles e do PostgreSQL saudável. Acesse [OpenAPI](http://localhost:8000/docs). O volume `postgres_data` preserva os dados em reinícios; não use `down --volumes` no ambiente de desenvolvimento.

## Iniciar o mobile

```bash
cd mobile
npm install
npx expo install --check
npm start
```

Configure `EXPO_PUBLIC_API_URL` em `mobile/.env`: Android Emulator usa `http://10.0.2.2:8000/api/v1`; dispositivo físico usa `http://IP_DO_COMPUTADOR:8000/api/v1`; web/iOS Simulator usa `http://localhost:8000/api/v1`. Reinicie o Metro após mudar o arquivo. Use `npm run android` para abrir no emulador existente, ou `npm run web` para a prévia no navegador.

Escolha um dos perfis retornados pela API e entre com a senha fictícia definida em `DEMO_PASSWORD`. Não há senha de usuário real. A sessão Bearer expira e o logout a revoga no servidor. O saldo confirmado é lido da API; os cenários/Pix visuais anteriores ficam explicitamente separados do ledger persistido.

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
