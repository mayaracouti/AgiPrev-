# Relatório de aceite integral do MVP AgiPrevê

Data: 23/10/2026. **Decisão: NO-GO para homologação integral.** A implementação integrada e os ensaios automatizados passaram, mas CA-08, CA-09 e CA-10 têm bloqueios/não verificações que impedem aprovar os dez critérios. Não há afirmação de homologação nativa ou qualidade classificatória comprovada.

## Coordenação, escopo e critérios

PO, DEV e QA foram lidos/aplicados nessa ordem. Por autorização explícita de uso de agentes, avaliação, experiência mobile e cenários/desempenho foram delegados, integrados e confrontados com a regressão final pelo coordenador. Sem dados reais, APIs Agibank, Supabase, Next.js ou microserviços. Preservados os cenários locais anteriores, identificados separadamente do ledger.

O repositório não continha descrições originais dos CT-001 a CT-018, CA-01 a CA-10 nem das TASK-031 a 040. Os IDs CT/CA foram tratados como critérios obrigatórios, com o mapeamento adotado em [sprints-05-07.md](requirements/sprints-05-07.md) e [roteiro](guides/demo-walkthrough.md). Não se apresenta esse mapeamento como catálogo original, nem se aprova uma tarefa sem sua evidência.

## Evidência executada

| Verificação | Resultado |
| --- | --- |
| Backend completo em FastAPI/PostgreSQL isolado | **87 passaram, zero skips, 54,72 s**; inclui migrações, contas, concorrência/idempotência, previsões, experimentos, alertas, falhas e CT-001 a 018. |
| Ruff check / format check | Passaram; **81 arquivos** formatados corretamente no estado final do código. |
| Mobile `npm run check` | TypeScript e Expo lint passaram; **47 testes Jest / 11 suítes** e suíte Node passaram. |
| Exportação Expo web | Passou, **979 módulos**, artefato `/tmp/agipreve-final-web`. Não substitui execução Android/iOS. |
| Compose de desenvolvimento | Build/up concluídos; PostgreSQL/API saudáveis; migração **0006_alerts_refresh (head)** e readiness `ok`. Seed idempotente concluiu. |
| Inicialização limpa e persistência | `scripts/verify_infrastructure.py` passou: projeto/volume exclusivos, migração/seed/health e registro mantido após reiniciar PostgreSQL. Somente recursos temporários desse projeto foram removidos. |
| Roteiro HTTP real | Login, previsão, hipótese sem débito, Pix idempotente, antes/depois, alerta/leitura, avanço virtual, experimento idempotente e exportações passaram na API em execução. |
| Organização / diferenças | `git diff --check` passou; personas preservadas; nenhum Markdown novo na raiz nem diretório de documentação de testes criado. |

Comandos principais executados na raiz, usando o código atual montado no container de testes:

```bash
docker compose -f compose.test.yaml run --rm -v "$PWD/backend:/app" -v /tmp:/evidence tests sh -c 'ruff check --no-cache . && ruff format --no-cache --check . && pytest -p no:cacheprovider -q --junitxml=/evidence/agipreve-backend-final.xml'
docker compose config --quiet
docker compose up --build -d
docker compose exec api alembic current
python3 scripts/verify_infrastructure.py
docker compose exec api python -m app.demo --seed 4241
```

Em `mobile/`: `npm run check` e `npm exec -- expo export --platform web --output-dir /tmp/agipreve-final-web`.

JUnit da execução: `/tmp/agipreve-backend-final.xml` (87 testes, zero falhas/skips). O teste HTTP foi executado com `urllib` contra o Uvicorn real, lendo senha fictícia apenas do ambiente e guardando resumo sem token. Evidências permanentes: [MVP_DEMO_EVIDENCE.json](MVP_DEMO_EVIDENCE.json), [MVP_EVALUATION_RESULTS.json](MVP_EVALUATION_RESULTS.json) e [MVP_PERFORMANCE_RESULTS.json](MVP_PERFORMANCE_RESULTS.json). O arquivo JSON de avaliação preserva o primeiro resultado; não se repetiu o holdout para escolher outro modelo.

Aviso não bloqueante: depreciação Starlette/httpx no TestClient. Nenhum teste nativo foi substituído por mock e chamado de entrega física: doubles Expo e HTTP são usados somente nos testes de componente/adaptador.

## CA-01 a CA-10

| Critério | Decisão | Evidência / impedimento |
| --- | --- | --- |
| CA-01 — stack e dados fictícios | APROVADA no escopo automatizado | Código, geração sintética, aviso demonstrativo, exportação Expo e Compose. |
| CA-02 — sessão e isolamento | APROVADA | Testes login/expiração/revogação e 401/404; contas, alertas e experimentos não vazam entre clientes. |
| CA-03 — integridade financeira | APROVADA | Decimal/NUMERIC, extrato reconciliado, 1000 clientes no teste de geração, repetição/concorrência sem duplicar débito. |
| CA-04 — previsões e corte | APROVADA | CTs e testes 7/15/30, identidade de saldo, estornos, disponibilidade, snapshots imutáveis; futuro observado sempre null. |
| CA-05 — Pix e recuperação | APROVADA na API/componentes | Ensaio HTTP e testes de falha injetada: ledger e evento duráveis, nova versão, referência anterior e retry sem novo débito. E2E físico não executado. |
| CA-06 — alertas e contexto | APROVADA na API/componentes | Configuração, deduplicação, leitura e autorização; excesso de gasto sem déficit não emite alerta; recomendação liga valor/data, sem crédito ou promessa. |
| CA-07 — rastreabilidade e relatórios | APROVADA | Experimentos imutáveis, seed/dataset/hiperparâmetros/artefato/métricas; idempotência, bloqueio de nova seleção no mesmo dataset final; filtros JSON/CSV/HTML. |
| CA-08 — avaliação final | BLOQUEADA para qualidade classificatória | Regressão calculada e reproduzível, mas holdout sem déficits realizados: Recall/F1/F2/lead time indefinidos; não há evidência de detecção generalizável de risco. |
| CA-09 — desempenho e notificação física | BLOQUEADA | CPU1000 medida; P95 HTTP/DB/E2E e renderização/refresh em dispositivo não medidos. Permissão/agendamento/abertura testados com doubles; entrega física não verificada. |
| CA-10 — homologação/demonstração | BLOQUEADA | Roteiro e ensaio HTTP preparados, mas navegação/acessibilidade Android/iOS e apresentação integral em dispositivo não executadas; descrições originais 031–040 ausentes. |

## Desempenho realmente medido

Ambiente: container Python **3.12.15**, Linux **6.14.0-37 x86_64**, 16 CPUs lógicas visíveis, ambiente compartilhado sem controle de carga. Dados `synthetic-v1`, seed42, 1000 clientes distintos, 30 dias, execução sequencial. Modelo treinado uma vez; suas amostras não incluem os demais clientes de inferência.

| Etapa | P95 | Máximo | Total |
| --- | --- | --- | --- |
| Inferência/projeção CPU, 1000 clientes | **0,016052 s** | 0,049866 s | 13,009 s |
| Recálculo CPU após gasto hipotético, 1000 clientes | **0,016236 s** | 0,058260 s | 13,105 s |

Treino único: **0,540008 s**. Checksum: **30000 pontos**. Exclui HTTP, PostgreSQL, fila, concorrência, renderização e retreino por cliente. A API operacional treina por execução; portanto esses P95 **não aprovam RNF-001 ponta a ponta**. O teste de banco com 1000 clientes comprova dados e reconciliação, não carga simultânea de 1000 sessões. TASK-054 permanece bloqueada nos escopos não medidos.

Reprodução: `python -m app.modules.forecasting.benchmark --count 1000 --seed 42 --output /tmp/agipreve-performance.json`, no backend com dependências. O arquivo permanente guarda os números da execução original.

## Avaliação temporal final

Avaliação offline: seis perfis, seed42, **144 registros** = quatro modelos × três horizontes × duas partições × seis perfis. Treino até **2026-07-01**, validação até **2026-08-01**, final até **2026-09-01**. O regressor é congelado antes da validação; seleção pela soma dos MAE de validação, antes de calcular holdout. Baselines: saldo constante, média móvel, sazonal ingênuo; híbrido: recorrências e boosting de árvores rasas. Registro persistente também exercitado na API/PostgreSQL.

Exemplos do holdout30 (valores exibidos arredondados; precisão completa no JSON):

| Perfil / modelo | MAE (R$) | MSE (R$²) | RMSE (R$) | Bias (previsto-real, R$) |
| --- | --- | --- | --- | --- |
| Regular / híbrido | 117,1543 | 18826,1145 | 137,2083 | 115,8323 |
| Regular / constante | 2359,1267 | 6386686,6522 | 2527,1895 | -2356,3580 |
| Variável / híbrido | 4102,8377 | 18703700,5230 | 4324,7775 | -4102,5937 |
| Variável / constante | 2692,0037 | 8360833,5496 | 2891,5106 | -2690,4530 |

O híbrido não vence todos os perfis: o método constante foi escolhido na validação dos perfis variável e sazonal. Isso está registrado, sem reescolher pelo holdout. O dataset não apresentou déficits positivos rotulados nesse período; Precision/Recall/F1/F2/lead time ficam `null` quando indefinidos. Não são zero nem aprovação da classificação. Fixtures com déficit verificam fórmulas e regras, mas não substituem validação classificatória em holdout representativo.

Limitações: dados de um gerador determinístico com regras mensais simples; nenhuma generalização a banco real, calibração de probabilidades, intervalo de confiança, disponibilidade99% ou desempenho nativo comprovados. Dados de avaliação disponíveis por conta respeitam autorização; os seis perfis offline são explicitamente sintéticos. Treino/seleção não devem ser refeitos no mesmo holdout para melhorar os números.

## Ensaio da demonstração

Seed de dados **4241**, seed do algoritmo **42**, conta fictícia `42bc85f7-99d1-5fbd-b2d8-78bf506e6e35`. Preparação por `app.demo` calculou despesa para deixar R$50,00; não sobrescreveu o saldo. O ensaio HTTP confirmou:

- Pix de R$10,00: **R$50,00 → R$40,00**, chave idempotente repetida sem duplicar.
- Previsão anterior `de97a1b7-a47f-4515-a642-781caaede77d`; nova `d742f734-105f-4202-b84c-0625da36851c`, status ready; versão anterior idêntica ao ser consultada.
- Diferença no primeiro ponto: **-R$10,38**, calculada pelas previsões. Ela inclui o retreino após a movimentação, portanto não deve ser descrita como impacto fixo de apenas R$10,00 em toda a curva.
- Alerta persistido e marcado lido, data virtual avançada a **2026-10-24**; futuro permaneceu sem observado.
- Experimento `64bf1222-a3f5-4884-8ea3-f0c3c7a610f4`, versão evaluation-v1, recuperado idempotentemente; exportações respondem com dados calculados.

A preparação atual não altera o holdout passado. Os IDs documentam essa execução, não são constantes de produção. O roteiro de 10 minutos está em [demo-walkthrough.md](guides/demo-walkthrough.md); a execução completa em dispositivo ainda não foi realizada.

## Defeitos e correções

- Regressão antiga contava quatro previsões após crédito; agora existem três originais, uma automática e uma manual. Teste atualizado para exigir cinco, verificar o UUID automático e preservar a imutabilidade.
- Filtro de holdout permitia alterar configuração e repetir seleção no mesmo dataset: passou a rejeitar com409 antes de calcular novamente; repetição exata retorna experimento anterior.
- Dashboard técnico ganhou controles reais de filtro, além de parâmetros URL, sobre registros autorizados.
- Pix/credito confirmam ledger e evento antes de chamar modelo. Falha injetada comprovou evento failed, saldo preservado, obsolescência visível e reprocessamento bem-sucedido.
- Avisos de imports/formatação corrigidos antes da suíte final. Timeout do teste de retry foi ampliado de1s para3s sem mudar seu resultado esperado; suíte final passou.

Não há falha automatizada conhecida pendente no estado final. Permanecem bloqueios de homologação listados acima; ausência de falha nos testes não os elimina.

## Auditoria de rastreabilidade das 58 tasks

A coluna de status respeita o alcance das evidências desta execução. Aprovação automatizada não equivale a homologação de dispositivo. As tarefas031–040 permanecem não verificadas por falta de suas definições originais.

| Task | Objeto | Status | Evidência / pendência |
| --- | --- | --- | --- |
| TASK-001 | Estrutura e stack | APROVADA (automatizado) | Compose limpo/health/persistência e exportação Expo. |
| TASK-002 | Docker e persistência | APROVADA (automatizado) | Compose limpo/health/persistência e exportação Expo. |
| TASK-003 | Ambiente | APROVADA (automatizado) | Compose limpo/health/persistência e exportação Expo. |
| TASK-004 | SQLAlchemy/Alembic | APROVADA (automatizado) | test_banking_integration, test_config, test_health, test_api_errors, testes mobile. |
| TASK-005 | HTTP e contratos | APROVADA (automatizado) | test_banking_integration, test_config, test_health, test_api_errors, testes mobile. |
| TASK-006 | Qualidade | APROVADA (automatizado) | test_banking_integration, test_config, test_health, test_api_errors, testes mobile. |
| TASK-007 | Navegação | BLOQUEADA no aceite integral | Router/check compila; navegação/acessibilidade nativa não executada. |
| TASK-008 | Clientes/contas | APROVADA (automatizado) | test_banking_integration, test_config, test_health, test_api_errors, testes mobile. |
| TASK-009 | Autenticação fictícia | APROVADA (automatizado) | test_banking_integration, test_config, test_health, test_api_errors, testes mobile. |
| TASK-010 | Saldo | APROVADA (automatizado) | test_banking_integration, test_config, test_health, test_api_errors, testes mobile. |
| TASK-011 | Transações/extrato | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-012 | Créditos | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-013 | Débitos | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-014 | Pix simulado | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-015 | Categorias | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-016 | Relógio virtual | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-017 | Gerador/perfis | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-018 | Histórico sintético | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-019 | Eventos extraordinários | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-020 | Recorrências | APROVADA (automatizado) | test_transactions_simulation, test_recurrences; geração/reconciliação1000 no PostgreSQL. |
| TASK-021 | Séries diárias | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-022 | Atributos | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-023 | Divisão temporal | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-024 | Contratos de previsão | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-025 | Baselines | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-026 | Receitas recorrentes | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-027 | Despesas recorrentes | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-028 | Despesas variáveis | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-029 | Saldo híbrido | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-030 | Versões imutáveis | APROVADA (automatizado) | test_forecasting, test_forecasting_integration; identidade/corte/versões e mobile. |
| TASK-031 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-032 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-033 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-034 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-035 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-036 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-037 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-038 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-039 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-040 | Definição original não disponível | NÃO VERIFICADA | Descrição/critério original ausente; não inferir aprovação de código sobreposto. |
| TASK-041 | Cenários financeiros | APROVADA (automatizado) | 18 CTs pytest; FinancialDashboard risco/sem risco. |
| TASK-042 | Experimentos | APROVADA (automatizado) | Experiment persistido/idempotente/imutável e ID/version HTML. |
| TASK-043 | Relatórios | APROVADA (automatizado) | JSON/CSV/HTML autorizados com controles/filtros; seis perfis offline. |
| TASK-044 | Dashboard | APROVADA (automatizado) | latest agregado e testes componente/data/horizonte. |
| TASK-045 | Real × previsto | APROVADA (automatizado) | series observado limitado ao relógio; futuro null; gráficos/zero. |
| TASK-046 | Desvios | APROVADA (automatizado) | desvio/base zero e ausência de alerta sem déficit. |
| TASK-047 | Regras de alertas | APROVADA (automatizado) | regras, severidade e dedup testados. |
| TASK-048 | Expo Notifications | BLOQUEADA no aceite integral | Adaptador e 2 testes Jest; entrega física Android/iOS não verificada. |
| TASK-049 | Central de alertas | APROVADA (automatizado) | Listagem/detalhe/read e isolamento PostgreSQL/mobile. |
| TASK-050 | Recomendações | APROVADA (automatizado) | Déficit/data explicam sugestão, sem garantia/crédito. |
| TASK-051 | Simulador | APROVADA (automatizado) | Teste API confirma ledger/saldo/forecasts inalterados; formulário/gráfico testados. |
| TASK-052 | Pix até reprevisão | APROVADA (automatizado) | API real + teste de falha/idem; before/after no componente. |
| TASK-053 | Integração | APROVADA (automatizado) | 87 pytest PostgreSQL e47 Jest; migrações e erros. |
| TASK-054 | Desempenho/carga | BLOQUEADA no aceite integral | CPU1000 medida; E2E concorrente e dispositivo não medidos. |
| TASK-055 | Observabilidade/falhas | APROVADA (automatizado) | Ledger durável, evento failed/ready, retry, correlação e logs JSON. |
| TASK-056 | Validação final | BLOQUEADA no aceite integral | 144 registros finais reproduzíveis; classificação indefinida sem déficits. |
| TASK-057 | Empacotar demonstração | APROVADA (automatizado) | Compose limpo/health/persistência e exportação Expo. |
| TASK-058 | Homologar MVP | BLOQUEADA no aceite integral | CA08/09/10 bloqueados: NO-GO. |

## Pendências para mudar a decisão

1. Executar Android/iOS: navegação, gráficos, acessibilidade básica, renderização/refresh e permissão/entrega/abertura de notificação local. Push remoto continua condicionado a build compatível.
2. Medir P95 no fluxo operacional com HTTP, PostgreSQL, recálculo e nível de concorrência documentado. O ensaio CPU não supre esse dado.
3. Definir prospectivamente um novo conjunto final representativo com déficits, sem reutilizar o holdout já visto para selecionar/ajustar modelos. Registrar métricas classificatórias e limites.
4. Recuperar ou formalizar com o responsável as descrições031–040 e o catálogo original CT/CA para fechar rastreabilidade normativa.
5. Executar e registrar a apresentação completa de10 minutos em dispositivo. O roteiro preparado e o ensaio HTTP não são essa apresentação.

Próxima atividade desbloqueada: validação nativa e medição operacional descritas acima; nenhum desses itens foi declarado aprovado sem execução.
