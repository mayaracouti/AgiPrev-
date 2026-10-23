# Refinamento PO — Fundação e banco simulado (TASK-001 a TASK-010)

## Escopo e precedência

Implementar e validar as dez tarefas solicitadas, preservando o frontend existente e usando apenas dados fictícios. A TASK-007 substitui a navegação anterior por Início, Extrato, Pix e AgiPrevê; a Conta passa a um fluxo auxiliar. O Laboratório continua fora da aplicação bancária.

Não incluir endpoints de criação de movimentações/Pix, motor preditivo, backtesting ou notificações push neste lote. Os fluxos visuais anteriores permanecem explicitamente locais. Nenhuma simulação pode substituir silenciosamente um saldo ou uma autenticação exigidos pela API.

## Entradas, saídas, dependências e aceite

| Task | Entradas / dependências | Saídas | Critérios verificáveis |
| --- | --- | --- | --- |
| 001 | Stack obrigatória e repositório existente | `mobile/` e `backend/` modulares; README | API inicia com Uvicorn; Expo inicia e gera bundle; comandos documentados |
| 002 | Docker, acesso ao daemon, registros de imagens e 001 | Compose, Dockerfile, volume e endereço de API | Build/up conclui; PostgreSQL e API saudáveis; registro persistido continua após reinício em projeto isolado |
| 003 | Exemplos de ambiente, 002 | Validação de URL, banco, CORS, senha demo e duração da sessão | Valores válidos iniciam; configurações inválidas são recusadas; `.env` não é rastreado pelo Git |
| 004 | PostgreSQL e 003 | Base SQLAlchemy, tipos e cadeia Alembic | Em schema limpo: upgrade/downgrade/upgrade; NUMERIC(18,2) inspecionado no banco |
| 005 | API e endereço configurados | Axios, timeout, contratos e erro estruturado | Rede, timeout, validação e falha de servidor são diferenciados; app mostra erro/retry sem saldo inventado; OpenAPI documenta contratos |
| 006 | Dependências instaladas e banco de teste | pytest/Ruff, Jest/RNTL, lint/typecheck e regressões | Comandos passam em instalação limpa; testes PostgreSQL não são substituídos por SQLite ou mocks |
| 007 | Expo Router, design existente e 005 | Quatro abas, componentes de loading/vazio/erro e GET /health | Rotas navegáveis em execução; cartão de conectividade confirma API e banco reais |
| 008 | 004 e PostgreSQL | Customer, Account, ledger inicial, seed e consultas | Cada perfil fictício tem exatamente uma conta; seed repetido não duplica conta ou crédito; modelo/conta não expõe hash de senha |
| 009 | 008 e senha demo configurada | Login, sessão com expiração/revogação, logout e autorização | Credenciais inválidas falham; token ausente, expirado ou revogado recebe 401; token de A não consulta conta/ledger/saldo de B |
| 010 | 008/009 | Consulta de saldo real e card com loading/erro | Soma de créditos menos débitos coincide com saldo; zero continua zero; resposta é string decimal com duas casas; erro não exibe fixture |

001–007 são a fundação. 008–010 usam a mesma API e banco; sua implementação pode avançar nas partes independentes enquanto o aceite de execução estiver bloqueado, mas não equivale à aprovação das dependências.

## Regras e casos-limite

- Um cliente possui uma conta BRL neste MVP. Não há cadastro de clientes reais ou importação de dados bancários.
- O seletor consulta perfis fictícios públicos (`id`, nome, e-mail e perfil). Não retorna contas, saldo ou senha antes da autenticação.
- A senha de desenvolvimento é definida no ambiente e usada apenas para os três perfis fictícios. É uma limitação deliberada da demonstração, não um modelo de identidade para produção. Não inventar credenciais pessoais.
- Sessões usam tokens aleatórios opacos; o banco armazena somente SHA-256 do token e hash PBKDF2 com salt da senha. Duração padrão de 60 minutos, configurável de 1 a 1440 minutos. Logout revoga no servidor; erros de revogação devem ser informados, sem declarar sucesso.
- Conta inexistente e conta de outro cliente retornam o mesmo 404, evitando enumeração. UUID inválido e parâmetros de paginação fora do intervalo retornam 422.
- O saldo persistido não possui coluna independente: é calculado por soma dos lançamentos confirmados. Ledger vazio retorna `0.00`. Crédito inicial é um lançamento idempotente; referências duplicadas e valores não positivos são rejeitados pelo banco.
- Valores do PostgreSQL são NUMERIC(18,2), Python usa Decimal e JSON usa strings decimais. A formatação no mobile não converte a string para ponto flutuante, inclusive no limite de 16 dígitos inteiros.
- Timeout, ausência de rede e 5xx não podem ser confundidos com saldo zero nem acionar fallback para cenários. Respostas antigas/canceladas não devem reaparecer após troca de conta ou atualização.
- Nunca executar downgrade, limpeza ou teste de persistência no banco de desenvolvimento. Os testes usam schema exclusivo em banco terminado em `_test`; o script de infraestrutura usa projeto/volume próprios.
- RNF-002 (99% de disponibilidade) e metas de escala não são comprovadas pelo simples startup; exigem avaliação específica posterior.

## Evidências e entrega

As três personas foram lidas na ordem solicitada. O DEV deve corrigir defeitos encontrados na revisão de QA e repetir as verificações afetadas. Resultados efetivos e pendências por tarefa ficam em [IMPLEMENTATION_STATUS](../IMPLEMENTATION_STATUS.md). Teste não executado é **não verificado**, nunca aprovado por inspeção.
