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

Não há endpoint de escrita de movimentações neste lote. O seed cria um crédito inicial por perfil, com referência única. Uma futura task de movimentações deverá implementar idempotência, transações atômicas e concorrência antes de conectar o Pix visual à conta persistida.

## Erros e OpenAPI

Erros usam `{"error":{"code":"...","message":"...","details":[]},"request_id":"..."}`. Validações incluem somente nome e código do campo, nunca input, senha ou contexto interno. 401 invalida a sessão no cliente (exceto erro de login); 404 protege contas inexistentes/alheias; 422 indica validação; 503 indisponibilidade do banco; 500 erro inesperado sem diagnóstico privado. OpenAPI documenta esses modelos e o esquema HTTP Bearer.

O cliente Axios usa timeout de 10 segundos, cancelamento e tratamento separado de rede, timeout, validação e servidor. Nenhuma falha se transforma em saldo zero ou fixture de sucesso. Hooks vinculam respostas à conta/versão da consulta e descartam requisições canceladas.

## Sessão e limitações

Senha: PBKDF2-SHA256 com salt exclusivo e 600.000 iterações. Token: 32 bytes aleatórios em base64url, somente hash SHA-256 persistido. Expiração e revogação são verificadas em cada consulta protegida. O app mantém o token apenas na memória e o descarta ao expirar; não há refresh token nem persistência de login nesta etapa.

A senha de desenvolvimento compartilhada entre perfis é exclusivamente para demonstração com dados fictícios e fica no `.env` local ignorado pelo Git. A listagem de perfis é pública para o seletor. Este ambiente local não oferece identidade de produção, TLS ou limitação de tentativas de login; não o exponha à internet.

## Persistência

`0001_baseline` foi preservada; `0002_accounts_auth_ledger` adiciona customers, accounts, ledger_entries e auth_sessions, com índices, chaves estrangeiras e constraints. O seed é um processo separado após migrações e não substitui senhas, contas ou créditos existentes. Alterar DEMO_PASSWORD depois do primeiro seed não altera hashes já persistidos; rotação de credenciais requer procedimento próprio posterior.
