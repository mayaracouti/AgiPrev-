# Desenvolvimento local

## Pré-requisitos

Docker Engine com permissão de acesso ao daemon e Docker Compose v2 ou superior. Node.js 22.13 ou superior (Node 24 LTS recomendado), npm, acesso aos registros npm e PyPI e Expo Go compatível com SDK 57 ou development build. Para executar o backend fora de containers, usar Python 3.12 ou 3.13 com suporte a venv.

O frontend inclui interações demonstrativas em memória; o backend de negócio será integrado posteriormente; consulte o [escopo](../requirements/mvp-scope.md).

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

O PostgreSQL precisa estar saudável; a tarefa `migrate` aplica `alembic upgrade head` e termina com código zero; então a API inicia com reload. O volume `postgres_data` preserva os dados entre reinicializações. A migração inicial cria somente o controle do Alembic, sem schema financeiro.

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

Use a mesma rede local e permita acesso à porta da API no firewall. Variáveis públicas entram no bundle, portanto não armazenam segredos. Reinicie o Metro depois de alterar o `.env`. Os endpoints de negócio ainda não existem. O frontend usa cenários locais e não faz requisições financeiras.

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

1. Selecione Gisele, Rafael ou Ana e entre no protótipo, sem usar credenciais reais.
2. Confira o saldo, oculte os valores e abra o extrato. Filtre por período e categoria ou busque pela descrição.
3. Registre uma receita, despesa ou Pix fictício. Tente valor inválido e uma saída acima do saldo. Confirme um valor válido uma única vez.
4. Veja o saldo atualizado e a comparação de cenário antes/depois na confirmação. Abra o AgiPrevê e consulte 7, 15 e 30 dias.
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

O log fornecido pelo usuário confirmou o build das imagens, PostgreSQL saudável e a tarefa de migração concluída com código zero. Isso atualiza o bloqueio anterior de inicialização no terminal do usuário; não significa acesso ao Docker liberado dentro desta sessão do agente.

Na implementação do frontend, a instalação npm foi novamente tentada e falhou por resolução DNS (`EAI_AGAIN`). Não foram gerados lockfiles nem declaradas validações de emulador, lint ou TypeScript completo sem as dependências. Com ferramentas recuperadas do cache, foram executados sete testes dos módulos puros, checagem estrita TypeScript do modelo demonstrativo e validação sintática de todos os arquivos TS/TSX. Os testes passaram. A execução visual no Android permanece pendente até a instalação completa.
