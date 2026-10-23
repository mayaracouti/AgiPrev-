# Estrutura e arquitetura

## Organização

```text
/
├── AGENTS.md
├── agents/personas/{po,dev,qa}.md
├── compose.yaml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── .env.example
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── api/                # REST e health checks
│   │   ├── core/               # Configuração por ambiente
│   │   ├── db/                 # Base, sessões e NUMERIC financeiro
│   │   └── modules/
│   │       ├── banking/
│   │       ├── forecasting/
│   │       └── notifications/
│   ├── migrations/versions/
│   └── tests/
├── mobile/
│   ├── package.json
│   ├── app.json
│   ├── tsconfig.json
│   ├── .env.example
│   ├── tests/                 # Testes das interações e regras demonstrativas
│   └── src/
│       ├── app/                # Acesso, três abas e fluxos auxiliares Expo Router
│       ├── components/         # Componentes compartilhados
│       ├── config/             # Variáveis públicas
│       ├── services/           # Cliente HTTP com Fetch e timeout
│       ├── theme/              # Tema inicial
│       ├── types/              # Contratos compartilhados
│       ├── demo/               # Estado e cenários determinísticos em memória
│       └── features/           # Limites dos módulos e configuração de avaliação
└── docs/
    ├── requirements/mvp-scope.md
    ├── architecture/project-structure.md
    └── guides/local-development.md
```

Os diretórios de módulos reservam os limites previstos no [escopo](../requirements/mvp-scope.md). Camadas internas de serviços, schemas, modelos e repositórios serão criadas conforme surgirem implementações reais, evitando estruturas vazias e abstrações antecipadas. Não foi necessário criar um `src/` na raiz.

## Backend e persistência

Um único processo FastAPI serve os módulos; eles compartilham o mesmo PostgreSQL. A futura API de negócio terá prefixo `/api/v1`. Não há microserviços ou chamadas a serviços bancários reais. O serviço Compose `migrate` é uma tarefa temporária que aplica migrações antes da API, não um serviço de negócio separado.

A sessão SQLAlchemy é criada por requisição e encerrada ao final. Futuras operações bancárias deverão delimitar explicitamente a transação e a política de concorrência e idempotência. Nenhum commit automático foi introduzido. O tipo compartilhado `MONEY` usa `NUMERIC(18, 2)` e `Decimal`; valores JSON devem ser strings decimais para evitar aritmética financeira com `float` ou `number`.

O Alembic está configurado com uma revisão inicial sem tabelas de negócio: ela inicializa a cadeia de migrações e sua tabela de controle. Novos modelos precisam ser importados no ambiente Alembic para geração e revisão das migrações. Nunca usar `create_all` como substituto de migrações versionadas.

`/health/live` verifica o processo; `/health/ready` consulta o banco e retorna 503 sem detalhes internos se ele estiver indisponível. Essas rotas não atestam migrações: no Compose, a aplicação bem-sucedida das migrações é uma dependência de inicialização separada.

## Mobile

React Native com Expo SDK 57, TypeScript estrito e Expo Router. As versões nativas seguem a [matriz do SDK 57](https://github.com/expo/expo/blob/sdk-57/packages/expo/bundledNativeModules.json). A biblioteca `react-native-chart-kit`, baseada em `react-native-svg`, renderiza curvas do cenário, despesas acumuladas, comparativos e simulações. `expo-linear-gradient` preserva os gradientes da referência visual. Expo Notifications está declarado e configurado como plugin; ainda não há solicitação de permissões ou envio de notificações.

O mobile executa no host com Expo e conecta à API HTTP. O Docker executa API, tarefa de migração e banco. Isso mantém o acesso a emuladores, QR Code e dispositivos no fluxo nativo do Expo, sem exigir container de Metro. O componente compartilhado `DemoNotice` identifica o protótipo nas telas. Não houve integração com o Supabase da referência.

### Estado demonstrativo

`src/demo/DemoProvider.tsx` compartilha a sessão e o estado entre abas. `src/demo/model.ts` contém fixtures determinísticas e regras locais, sem chamadas HTTP ou treino de modelos. Valores financeiros são centavos inteiros na memória do frontend; a conversão para reais ocorre apenas na apresentação e nos gráficos. A futura fronteira REST mantém strings decimais e o backend mantém Decimal/NUMERIC.

A sessão começa por seleção de perfil fictício. As rotas internas usam `Stack.Protected`; essa proteção organiza a navegação e não substitui autenticação/autorização no servidor.

Cada movimentação confirmada gera uma versão ilustrativa de 30 dias com data de geração, horizonte, nome/versão do cenário, saldo de referência, motivo e pontos diários. A interface permite selecionar 7, 15 ou 30 dias. Uma confirmação repetida com o mesmo identificador não altera o saldo novamente. O formulário também impede reenvio após sucesso.

O avanço do relógio materializa movimentações sintéticas somente até a data alcançada. Versões antigas permanecem imutáveis. A comparação considera apenas dias já realizados e o histórico de versões alinha as curvas pelas mesmas datas. O simulador hipotético não cria transações nem snapshots.

As regras fixas consideram R$ 45/dia, salário no dia 5, aluguel no dia 8 e contas no dia 28; não são detecção automática de recorrência ou modelo validado. A geração de realizados usa valores sintéticos diferentes dos previstos para demonstrar desvios. Não há avaliação estatística sendo apresentada como resultado dessas regras.

`src/features/evaluation/report.ts` mantém uma estrutura técnica para configuração de experimento e relatório, sem tela ou aba no aplicativo. A avaliação de modelos pertence a um ambiente técnico separado, a ser desenvolvido futuramente. Métricas são `null` e o status é `awaiting_backend`. O app não simula que executou backtesting, calculou incerteza, mediu p95 ou detectou degradação. A preferência de alertas controla o destaque visual no início; não solicita permissões ou envia push.

Todos os dados são voláteis. Reiniciar o app, entrar novamente ou regenerar o cenário reinicia a demonstração. A integração futura deverá substituir os adaptadores locais por serviços REST e persistir transações, relógio, previsões, alertas e experimentos.

## Configuração e segurança local

O container Python usa usuário sem privilégios. PostgreSQL publica a porta somente em loopback e possui volume persistente. A API publica a porta 8000 para permitir acesso por celular na rede local; este Compose é para desenvolvimento com dados fictícios, sem autenticação ou TLS. Não expor esse ambiente à internet.

As credenciais ficam em arquivos `.env` ignorados pelo Git. `.env.example` usa placeholders. Nunca colocar segredos em `EXPO_PUBLIC_*`, respostas HTTP ou logs. CORS utiliza origens explícitas e não substitui autenticação. Dependências Python têm intervalos de versão delimitados; a resolução exata e os lockfiles permanecem pendentes enquanto os registros de pacotes não estiverem acessíveis.

Procedimentos e limitações verificadas estão no [guia local](../guides/local-development.md).
