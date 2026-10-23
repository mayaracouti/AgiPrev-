# TASK-041 a 058 — avaliação, alertas e integração

## PO — escopo e dependências

Autorização: solicitação das TASK-041 a 058 e prompts 59/60. Coordenação PO → DEV → QA, com frentes delegadas explicitamente autorizadas pelo usuário. Preservar código e evidências anteriores. Usar somente FastAPI, SQLAlchemy/Alembic/PostgreSQL e React Native/Expo/TypeScript. Dados e operações bancárias são inteiramente fictícios.

Entradas comuns: ledger confirmado, relógio virtual, forecasts imutáveis, seed e versões do dataset/modelo. Saídas: avaliação temporal persistida, relatórios, dashboard, comparação realizada, alertas e recuperação do recálculo. Dependências existentes: TASK-001 a 030. As descrições originais de TASK-031 a 040 não estão no repositório; não declarar essas tarefas aprovadas por sobreposição funcional.

## Critérios por tarefa

| Task | Regra verificável e limites |
| --- | --- |
| 041 | CT-001 a CT-018 executáveis em pytest e telas de risco/sem risco testadas. Mapeamento dos CT em `demo-walkthrough.md`; IDs são obrigatórios, as descrições são o mapeamento adotado nesta implementação, pois o catálogo original não foi fornecido. |
| 042 | Persistir seed, dataset, hiperparâmetros, árvore/coeficientes e versão/modelo/métricas. Experimento com UUID, imutável e idempotente por configuração/dataset. ID e versão no relatório técnico. |
| 043 | Relatórios autorizados JSON/CSV/HTML, filtros modelo/horizonte/perfil/partição, métricas calculadas e gráficos. Laboratório separado das quatro abas bancárias. Não agregar contas alheias para comparar perfis. CLI produz avaliação dos seis perfis sintéticos. |
| 044 | Última previsão agregada com saldo confirmado, futuro, receitas, risco, data-base, horizonte e indicação de obsolescência; não gerar previsão ao consultar. |
| 045 | Série da versão escolhida alinhada por data. Observado somente até o relógio virtual; futuro = null. Gráfico com linha zero e distinção textual. |
| 046 | Desvio de gastos acumulado sobre dias realizados da previsão, diferença real-previsto e percentual; denominador zero resulta null. Excesso isolado não cria alerta sem previsão atual de déficit. |
| 047 | Alerta somente por saldo previsto negativo, severidade pela proximidade em dias, regras habilitar/desabilitar e janela crítica 0..30. Deduplicação por conta/data de risco; explicação identifica versão e data. |
| 048 | Permissão de notificações locais por ação explícita; tratar negação e abertura autorizada para conta atual. Adaptador Expo real; doubles apenas nos testes. Entrega física deve ser verificada em Android/iOS; push remoto não habilitado sem build compatível. |
| 049 | Alertas persistentes; listar/detalhar/marcar lido com propriedade da conta; conta alheia 404. Leitura idempotente. |
| 050 | Recomendar revisão de gastos/datas até o déficit, a partir do montante/data efetivos. Sem promessa de resultado, oferta de crédito ou falsa probabilidade. |
| 051 | Gasto hipotético positivo em string decimal; recalcular curva sem escrever ledger, saldo, snapshot ou alerta. Permitir simular montante acima do saldo para explorar impacto. |
| 052 | Ledger e evento de recálculo confirmados juntos; após commit, gerar previsão/alerta. Receipt informa IDs anterior/novo, status e correlation ID. Retry da mesma chave não duplica débito nem previsão. |
| 053 | FastAPI com PostgreSQL isolado, migrações upgrade/downgrade e fluxos positivos/negativos; Axios/contratos/erros testados. Sem mock como funcionalidade de produção. |
| 054 | Medir CPU com 1000 clientes e distinguir do P95 HTTP/DB/E2E; meta 2s não aprovada sem medir o escopo correspondente. Renderização/refresh precisam de dispositivo. Registrar bloqueios concretos. |
| 055 | Evento durável pending/ready/failed, retries autorizados; falha ML não desfaz transação confirmada. Logs JSON com correlação e duração, contadores locais ao processo; sem tokens/senhas nos logs. |
| 056 | Treinar até train_end, selecionar só validação, congelar seleção antes de holdout; registrar MAE/MSE/RMSE/Bias/Precision/Recall/F1/F2/lead time. Repetição exata recupera experimento; nova seleção no mesmo dataset final retorna 409 antes de reavaliar. Métricas com denominador zero são null. Não retocar holdout após conhecer resultados. |
| 057 | Compose aplica migrações/seed e aguarda saúde; persistência comprovada em projeto descartável. README e roteiro explicam Expo, dados fictícios e preparação idempotente. |
| 058 | Executar CA-01 a CA-10; nenhum bloqueador aberto para GO. Teste não executado permanece não verificado, impedindo homologação integral. |

## CA-01 a CA-10 — matriz adotada para homologação

As descrições originais desses IDs não foram encontradas. Este mapeamento operacionaliza os requisitos enviados e não é apresentado como recuperação de um catálogo original. Os dez IDs são obrigatórios; a aprovação depende de evidência executada.

| Critério | Verificação |
| --- | --- |
| CA-01 | Stack, dados fictícios, arquitetura e identificação demonstrativa. |
| CA-02 | Login, sessão e isolamento entre clientes/contas. |
| CA-03 | Saldo Decimal/NUMERIC, extrato, idempotência e atomicidade. |
| CA-04 | Previsões 7/15/30, causalidade, evolução do saldo e versões imutáveis. |
| CA-05 | Pix com reprevisão, antes/depois, correlação e recuperação de falha. |
| CA-06 | Desvios/alertas/recomendações coerentes e central autorizada. |
| CA-07 | Experimentos rastreáveis, seleção temporal e exportações. |
| CA-08 | Avaliação final com evidência de regressão e classificação, incluindo limitações dos eventos de risco. |
| CA-09 | P95 no fluxo-alvo e 1000 clientes, sem substituir E2E por CPU; notificações locais entregues em dispositivo. |
| CA-10 | Navegação/acessibilidade básica em dispositivo e demonstração guiada integral, com rastreabilidade das 58 tasks. |

Resultados e decisão em [MVP_ACCEPTANCE_REPORT.md](../MVP_ACCEPTANCE_REPORT.md). Roteiro e CT em [demo-walkthrough.md](../guides/demo-walkthrough.md).
