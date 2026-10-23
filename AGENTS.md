# Instruções do projeto

## Etapa atual — Sprints 1 e 2, TASK-001 a TASK-010

A tarefa atual autoriza completar e validar fundação, infraestrutura, ambiente, persistência, contratos de API, qualidade, navegação, clientes/contas, autenticação fictícia e consulta de saldo, no frontend e backend. Seguir o refinamento em `docs/requirements/sprints-01-02.md` e atualizar `docs/IMPLEMENTATION_STATUS.md` com evidências por task. Não aprovar tarefas sem execução dos critérios; registrar bloqueios e testes não verificados.

A TASK-007 define agora as abas Início, Extrato, Pix e AgiPrevê. Preservar a Conta como fluxo auxiliar. O Laboratório de avaliação não é uma aba da aplicação. A orientação anterior de três abas foi substituída explicitamente pela task atual.

Manter as simulações explicitamente identificadas. Não apresentar regras locais como modelo treinado ou métricas não calculadas como resultados. Login e saldo confirmado devem usar a API, sem fixtures substituindo falhas. Preservar cenários visuais anteriores separados do ledger persistido. Não usar Supabase do wireframe: a integração futura será com a API FastAPI do projeto.

Adotar React Native, Expo, TypeScript e Expo Router no mobile; Python, FastAPI, Pydantic, SQLAlchemy 2.x e Alembic no backend; PostgreSQL e Docker Compose na infraestrutura. O backend é um monólito modular com API REST. Não utilizar Next.js nem microserviços.

Todos os dados bancários devem ser fictícios. Não integrar APIs reais do Agibank. A interface deve indicar que é um protótipo demonstrativo não oficial, com dados fictícios. Valores financeiros devem utilizar Decimal no Python e NUMERIC no PostgreSQL; transportar valores como strings decimais no JSON.

Código em `mobile/` e `backend/`. Consulte `docs/requirements/mvp-scope.md`, `docs/architecture/project-structure.md` e `docs/guides/local-development.md` antes de ampliar a implementação. Não criar Markdown vazio nem reorganizar arquivos fora do escopo autorizado.

## Personas e responsabilidades

- `@agentePO`: instruções em `agents/personas/po.md`. Manter requisitos, regras de negócio e critérios de aceite em `docs/requirements/`, quando a tarefa autorizar essa documentação.
- `@agenteDev`: instruções em `agents/personas/dev.md`. Manter documentação técnica em `docs/architecture/`, decisões arquiteturais em `docs/decisions/` e orientações técnicas em `docs/guides/`, quando necessário e autorizado.
- `@agenteQA`: instruções em `agents/personas/qa.md`. Utilizar os diretórios de documentação existentes e propor a localização de planos, cenários e evidências de testes. Propor `docs/testing/` antes de criá-lo, caso documentação permanente de testes seja necessária.

Os arquivos de personas devem permanecer exclusivamente em `agents/personas/`.

## Organização obrigatória

- Este `AGENTS.md` é o único Markdown de configuração de agentes permitido na raiz. Preservar arquivos convencionais existentes, como `README.md`, `CONTRIBUTING.md` e arquivos exigidos por ferramentas.
- Requisitos: `docs/requirements/`.
- Arquitetura: `docs/architecture/`.
- Decisões arquiteturais: `docs/decisions/`.
- Guias e procedimentos: `docs/guides/`.
- Adaptar a organização à arquitetura existente. Não mover nem recriar código-fonte para corresponder a uma estrutura de referência.
- Não criar Markdown temporário na raiz, documentação duplicada, diretórios sem finalidade ou documentos sem conteúdo real.
- Usar nomes descritivos e consistentes.

## Manutenção do contexto

Antes de criar um Markdown, procurar um documento com a mesma finalidade, identificar sua categoria e preferir atualizar o existente quando apropriado. Evitar fragmentar informações relacionadas, manter referências válidas e remover redundância ou conteúdo obsoleto quando a tarefa autorizar. Não armazenar credenciais ou dados sensíveis na documentação.

## Validação da configuração

Ao concluir, verificar a localização dos arquivos, a ausência de novos Markdown desorganizados na raiz, a validade dos caminhos deste arquivo, a ausência de documentos duplicados e o respeito à estrutura existente. Apresentar a árvore criada ou modificada e informar qualquer pendência que impeça concluir a configuração.

## Uso das personas

O protocolo abaixo autoriza a aplicação sequencial das três personas dentro do escopo de cada tarefa. Não implica delegação automática, criação de subagentes ou autorização para ampliar o escopo. Distinguir fatos, hipóteses e pendências.

## Protocolo obrigatório para todos os prompts

Antes de executar a tarefa, verificar a presença e ler os três arquivos: `agents/personas/po.md`, `agents/personas/dev.md` e `agents/personas/qa.md`. Se qualquer arquivo estiver ausente, informar qual está faltando e interromper o fluxo dependente; não inventar seu conteúdo.

1. **PO:** refinar a tarefa, definir entradas, saídas, regras de negócio, dependências e critérios verificáveis. Sinalizar ambiguidades antes de decisões irreversíveis.
2. **DEV:** inspecionar o código existente e implementar frontend/backend conforme o escopo autorizado. Criar migrações e testes quando necessários, executar os comandos disponíveis e registrar os arquivos criados ou alterados.
3. **QA:** construir cenários positivos, negativos e de borda, executar testes, verificar critérios de aceite e registrar evidências e defeitos. Havendo defeitos, devolver ao DEV para correção e repetir a validação afetada.

Em perguntas, revisões ou tarefas apenas documentais, aplicar o protocolo proporcionalmente, sem implementar funcionalidades, criar migrações ou produzir testes sem necessidade. Indicar itens não aplicáveis.

### Saída de cada execução

Apresentar:

- Resumo de requisitos, incluindo entradas, saídas, regras e dependências pertinentes.
- Arquivos criados ou alterados.
- Endpoints e migrações, ou indicação de que não houve alterações.
- Comandos executados e resultados de testes.
- Critérios atendidos e não atendidos; distinguir os não verificados.
- Riscos e pendências.
- Próxima tarefa desbloqueada, sem iniciá-la fora do escopo autorizado.

Se um teste não puder ser executado, registrar como **não verificado**, com o motivo. Não confundir teste proposto com teste executado, não inventar evidências nem declarar aprovação sem verificação. Registrar evidências e defeitos no relato da tarefa; criar documentação permanente somente quando necessária e autorizada, respeitando a organização existente.
