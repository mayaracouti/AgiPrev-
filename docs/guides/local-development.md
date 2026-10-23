# Desenvolvimento local

## Pré-requisitos

Docker Engine com permissão de acesso ao daemon e Docker Compose v2 ou superior. Node.js 22.13 ou superior (Node 24 LTS recomendado), npm, acesso aos registros npm e PyPI e Expo Go compatível com SDK 57 ou development build. Para executar o backend fora de containers, usar Python 3.12 ou 3.13 com suporte a venv.

O frontend consulta clientes, sessão, saldo e extrato na API; cenários e Pix visuais continuam locais; consulte o [escopo](../requirements/mvp-scope.md).

## Configuração

Execute na raiz, copiando somente os arquivos que ainda não existirem:

```bash
cp -n .env.example .env
cp -n backend/.env.example backend/.env
cp -n mobile/.env.example mobile/.env
```

Neste workspace esses três `.env` locais já foram criados, com uma senha aleatória de desenvolvimento compartilhada pelo Compose e pela configuração do backend local. Não sobrescreva essas configurações se já tiver dados persistidos no banco. Em outro checkout, substitua os placeholders: mantenha a senha da raiz e da URL do backend local coerentes. Prefira senha hexadecimal; caracteres reservados exigem percent-encoding na URL de conexão.

O Compose lê o `.env` da raiz e usa `db:5432` internamente. A API executada fora do Docker lê `backend/.env`, com `localhost` e a porta publicada do PostgreSQL. Reinicie a API ao alterar configuração.

## Iniciar containers

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps -a
docker compose logs api migrate
```

O PostgreSQL precisa estar saudável; a tarefa `migrate` aplica `alembic upgrade head` e termina com código zero; então a API inicia com reload. O volume `postgres_data` preserva os dados entre reinicializações. A revisão 0001 inicia a cadeia; a 0002 cria clientes, contas, ledger e sessões. O serviço seed cria os perfis fictícios idempotentemente.

Acesse `http://localhost:8000/docs`, `http://localhost:8000/health/live` e `http://localhost:8000/health/ready`. Ajuste a porta se tiver alterado `API_PORT`.

## Instalar e iniciar o mobile

```bash
cd mobile
npm install
npx expo install --check
npm run check
npm start
```

Após a primeira instalação bem-sucedida, versionar o `package-lock.json` gerado e utilizar `npm ci` nas instalações seguintes. Não utilizar `--force` nem `--legacy-peer-deps` para contornar incompatibilidades.

Ajuste `EXPO_PUBLIC_API_URL` em `mobile/.env` antes de iniciar:

| Ambiente | URL de exemplo |
| --- | --- |
| Simulador iOS no mesmo computador | `http://localhost:8000/api/v1` |
| Emulador Android padrão | `http://10.0.2.2:8000/api/v1` |
| Celular físico | `http://IP_LOCAL_DO_COMPUTADOR:8000/api/v1` |

Use a mesma rede local e permita acesso à porta da API no firewall. Variáveis públicas entram no bundle, portanto não armazenam segredos. Reinicie o Metro depois de alterar o `.env`. Os endpoints de negócio existem em /api/v1. Login e saldo confirmado exigem API disponível e não usam fallback local.

Abra o projeto pelo QR Code ou use `npm run android` / `npm run ios` com os respectivos emuladores instalados. iOS Simulator exige macOS. Consulte a [criação de projetos Expo](https://docs.expo.dev/more/create-expo/) para compatibilidade com Expo Go durante transições de SDK. Notificações push exigem as condições de dispositivo e build descritas na [documentação Expo Notifications](https://docs.expo.dev/versions/latest/sdk/notifications/); a dependência instalada não configura credenciais de push.

## Backend sem container

Suba o banco com `docker compose up -d db` na raiz. Depois:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verificações

No diretório `backend`, com dependências instaladas:

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pytest
.venv/bin/alembic upgrade head --sql
```

Os testes unitários de saúde usam dependências substituídas e não exigem banco ativo. Verificam liveness, execução da consulta de readiness, resposta 503 sem detalhes internos e o tipo NUMERIC/Decimal. Eles não substituem uma validação de integração real com PostgreSQL.

Alternativamente, na raiz com os containers disponíveis:

```bash
docker compose run --rm api pytest -p no:cacheprovider
docker compose exec api alembic current
```

Ao criar modelos, importar seus metadados em `backend/migrations/env.py`, gerar a revisão, revisar o SQL e testar upgrade/downgrade em um banco descartável. Exemplo na raiz:

```bash
docker compose run --rm -v ./backend/migrations:/app/migrations --user "$(id -u):$(id -g)" api alembic revision --autogenerate -m "descricao_da_alteracao"
docker compose run --rm migrate
```

Recriar a imagem após alterar dependências ou migrações, pois somente código da aplicação e testes são montados com reload. Antes de aplicar novas migrações via container, executar `docker compose build` para incluí-las nas imagens.

Para encerrar sem remover dados:

```bash
docker compose down
```

## Roteiro de demonstração do frontend

1. Selecione Gisele, Rafael ou Ana retornados pela API e entre com DEMO_PASSWORD de desenvolvimento, sem usar credenciais reais.
2. Confira o saldo, oculte os valores e abra o extrato. Filtre por período e categoria ou busque pela descrição.
3. No cenário visual separado, registre uma receita, despesa ou Pix fictício. Tente valor inválido e uma saída acima do saldo. Confirme um valor válido uma única vez.
4. Veja o saldo do cenário atualizado (o ledger e saldo confirmado no servidor não são alterados) e a comparação de cenário antes/depois na confirmação. Abra o AgiPrevê e consulte 7, 15 e 30 dias.
5. Em Versões, compare a previsão selecionada com a atual nas mesmas datas. Cada versão mostra metadados e os pontos diários.
6. Na Conta, avance 1 ou 7 dias e retorne ao Real × previsto. Somente datas já realizadas aparecem nessa comparação.
7. Use o perfil de orçamento apertado para observar alertas de déficit. Abra o histórico, marque um alerta como lido e avance até sua data para visualizar o resultado sintético posterior.
8. No simulador, compare um gasto hipotético; o saldo e as versões salvas não devem mudar.
9. Na Conta, regenere o histórico com uma semente e confirme a substituição dos dados. A mesma combinação de perfil/semente é reproduzível. Saia para trocar de perfil.

## Verificações do frontend

```bash
cd mobile
npm run check
npm run android
```

`check` reúne TypeScript, lint e testes. Os testes usam o runner nativo do Node e TypeScript para carregar os módulos puros, sem exigir emulador. Eles cobrem centavos, entrada inválida, histórico reproduzível, confirmação única, versões preservadas, integridade temporal, cenário sem débito e ausência de métricas fabricadas. Não substituem testes visuais e de integração no Android/iOS.

## Estado de validação

As evidências atuais por task estão em [IMPLEMENTATION_STATUS](../IMPLEMENTATION_STATUS.md). Os comandos foram executados em 23/10/2026: PostgreSQL real via Compose, testes backend, Ruff, instalação limpa npm, TypeScript, lint, Jest e exportação web. Validação visual Android/iOS não foi executada.

Para repetir integração sem tocar no banco de desenvolvimento, execute na raiz:

```bash
docker compose -f compose.test.yaml up --build --abort-on-container-exit --exit-code-from tests
python3 scripts/verify_infrastructure.py
```

O primeiro comando usa banco descartável terminado em `_test`; o segundo cria projeto e volume exclusivos para comprovar persistência após reinício. Migrações destrutivas são executadas somente em schemas de teste isolados.


## Banco simulado persistido e dados sintéticos — TASK-011 a TASK-020

Depois de atualizar os arquivos, aplicar as migrações em vez de recriar o banco:

```bash
docker compose up --build -d
```

No app, Receber/Pagar/Pix abrem revisão e confirmação pela API. O comprovante e o extrato são persistidos. O extrato oferece período, descrição, categoria e direção, paginação por cursor e edição de categoria. O saldo do início é atualizado após confirmação. As regras visuais antigas permanecem em Conta → Movimentação no cenário visual local.

Para gerar o conjunto completo (operação administrativa local e exclusivamente fictícia):

```bash
docker compose exec api python -m app.modules.simulation.generator --seed 42 --count 1000
```

Gera seis perfis e 158 mil transações realizadas nos 365 dias anteriores a 23/10/2026, mais 36 mil eventos pendentes para um ano. O seletor público permite escolher perfil e navegar por páginas; os clientes gerados usam a DEMO_PASSWORD fictícia configurada. Cada senha recebe salt próprio; essa etapa pode levar alguns minutos para 1000 clientes. Não usar senhas pessoais.

A mesma seed/índice reproduz IDs e dados financeiros (`synthetic-v1`); timestamps operacionais e hashes/salts de autenticação não compõem a comparação. Reexecutar a mesma seed pula clientes existentes sem substituir suas movimentações. Para comparar conjuntos novos, use seeds distintas ou bancos descartáveis; não limpe o banco de desenvolvimento.

Conta → Área dev mostra resumo, relógio persistido e eventos. Avance por data AAAA-MM-DD; a data não retrocede. Para atrasar salário, informe a data de um salário ainda pendente. Compra extraordinária e receita eventual são agendadas e afetam somente o saldo agendado até o avanço. Eventos podem produzir saldo negativo, mas débitos manuais e Pix recusam insuficiência. Recorrências do histórico persistido também aparecem no AgiPrevê, separadas dos gráficos do cenário visual anterior.

Validação objetiva:

```bash
docker compose -f compose.test.yaml run --rm -v "$PWD/backend:/app" tests pytest -p no:cacheprovider -s
cd mobile
npm run check
```

O volume do exemplo é somente para executar os testes com o código atual; a configuração de testes ignora `.env` locais. A geração completa é comprovada em PostgreSQL descartável, sem alterar dados de desenvolvimento. Evidências em [IMPLEMENTATION_STATUS](../IMPLEMENTATION_STATUS.md).

## Séries e previsões persistidas (TASK-021 a 030)

Aplicar `alembic upgrade head` até `0004_forecasts` antes de usar os endpoints de previsão. No AgiPrevê, o cartão de histórico persistido gera estimativas pela API e lista versões; os cenários locais anteriores continuam separados. Sem histórico suficiente, a versão informa `hybrid-insufficient-history-v1`.

Exportação reprodutível (substituir UUID e datas por uma conta com histórico suficiente; executar em `backend/`):

```bash
python -m app.modules.forecasting.datasets --account UUID --cutoff 2026-10-23 --train-end 2026-04-30 --validation-end 2026-08-31 --destination /tmp/agipreve-datasets --seed 42
python -m app.modules.forecasting.laboratory --account UUID --cutoff 2026-07-01 --validation-end 2026-08-31 --horizon 30 --output /tmp/agipreve-laboratory.html
```

O primeiro comando cria manifesto e arquivos separados de treino, validação e holdout em diretório identificado pelo SHA-256. O segundo gera uma interface HTML de comparação dos três baselines e JSON com curvas e MAE de saldo calculado sobre valores realizados. Não usar o holdout para escolher o modelo; a comparação rejeita horizontes além do limite de validação. A geração do relatório não adiciona uma aba ao banco.

Na exportação com fontes do ledger, cada partição contém `series` e `observations` com disponibilidade preservada até seu limite. Imports tardios ficam fora do treino anterior à sua chegada; a versão também incorpora as fontes. Ao construir atributos a partir dessas observações, usar sempre o corte por origem do pipeline, nunca tratar todos os dados da partição como disponíveis em todas as suas datas.

## Entrega integrada e homologação — TASK-041 a 058

O estado mais recente substitui as descrições históricas de previsão/alerta apenas local: backend em `0006_alerts_refresh` serve previsão, comparação, simulador, experimentos/relatórios e central persistida. A UI distingue esses fluxos dos cenários locais anteriores. Veja [contratos](../architecture/api-contracts.md) e [relatório integral](../MVP_ACCEPTANCE_REPORT.md).

Roteiro com seed dedicada, Pix, previsão anterior, alerta e métricas: [demo-walkthrough.md](demo-walkthrough.md). Preparar com `docker compose exec api python -m app.demo --seed 4241`; essa conta de demonstração já foi usada no ensaio de aceite. Repetir a seed preserva seu saldo/relógio, não faz reset. Use outra seed para começar uma nova sessão do zero.

A suíte final e a exportação web passaram, mas homologação integral é NO-GO pelos bloqueios nativos, de desempenho operacional e de cobertura classificatória descritos no relatório. O laboratório técnico é autenticado e separado da navegação bancária; métricas indefinidas não são substituídas por números ilustrativos.
