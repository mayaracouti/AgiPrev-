# Preparação de dados e motor de previsão — TASK-021 a TASK-030

## Escopo e dependências

Refinamento PO das tarefas autorizadas em 23/10/2026. Depende do ledger, relógio e recorrências das TASK-011 a 020 presentes no workspace. Mantém FastAPI, SQLAlchemy, Alembic, PostgreSQL e Expo; dados exclusivamente fictícios. O laboratório é técnico e separado da navegação bancária. Alertas, notificações, seleção automática do melhor modelo e reprevisão automática após Pix ficam para suas próprias tarefas.

## Entradas, saídas e regras verificáveis

| Task | Entrada → saída | Regra / aceite |
| --- | --- | --- |
| 021 | Ledger com referência, data econômica, disponibilidade e estorno → dias agregados com referências auditáveis | Uma referência idêntica conta uma vez; conflito falha. Lacunas são zero. Estorno integral inverte o fluxo original na data de lançamento; não apaga o histórico. Estorno órfão, encadeado, duplicado ou de valor divergente falha. |
| 022 | Histórico disponível no corte → atributos numéricos | Lags 1/7, média e desvio populacional de 7 dias, calendário, contagem de recorrências e dias até próxima receita. Histórico estritamente anterior ao alvo; padrões recalculados em cada origem de treino. Sem receita conhecida, dias até receita = -1. |
| 023 | Série, limites de treino/validação, horizonte e seed → partições e manifesto SHA-256 | Ordem temporal, datas únicas, partições não vazias; expurgar origens cujos rótulos atravessariam a fronteira. Holdout em arquivo separado, excluído da comparação para seleção. Versão inclui conteúdo, limites, horizonte e seed. |
| 024 | Conta autenticada, método e horizonte 7/15/30 → ForecastRun com pontos diários | Data-base do relógio persistido, versão de modelo/dataset, risco de saldo negativo e valores monetários como strings. Outros horizontes recebem 422; conta alheia recebe 404. |
| 025 | Histórico até corte → saldo constante, média móvel de 7 dias, sazonal ingênuo semanal | Determinísticos; média usa histórico disponível; sazonal repete última semana. Laboratório gera HTML/JSON com MAE efetivamente calculado em validação realizada, sem acessar holdout. |
| 026 | Pelo menos três receitas mensais regulares → eventos previstos | Valor mediano e periodicidade mensal observada; vencimento limitado ao último dia do mês. Regularidade observada não é probabilidade; incerteza explicitamente não calibrada. |
| 027 | Despesas mensais regulares → contas fixas | Mesmo calendário; retirar grupos recorrentes da despesa variável, um evento por descrição normalizada/direção/data. Estornos não contam como nova recorrência. |
| 028 | Amostras causais de despesas variáveis → regressor treinado reproduzível | Boosting determinístico de árvores de profundidade 1, equivalente de menor complexidade ao XGBoost para o MVP. Sem identificador de cliente nos atributos; aceita inferência fora do conjunto de treino. Saída limitada a zero. Sem sete dias anteriores, fallback zero identificado como histórico insuficiente, sem alegar treino. |
| 029 | Saldo realizado no corte + fluxos previstos → saldo diário | Decimal nas fronteiras e centavos quantizados. Saldo[d] = saldo[d-1] + receita[d] - fixa[d] - variável[d], para 7/15/30. |
| 030 | Execução e pontos → snapshot persistido consultável | Novos UUIDs por execução; metadados e payload preservados. PostgreSQL rejeita UPDATE/DELETE de runs e pontos; novas movimentações não alteram versões anteriores. |

## Casos-limite e decisões do MVP

- Histórico vazio: série diária zerada e estimativa explicitamente sem histórico suficiente. Sem intervalo de confiança fabricado.
- Dias são datas do relógio simulado, sem conversão implícita de fuso. `available_on` registra disponibilidade econômica no ambiente simulado; importações históricas existentes recebem a data econômica na migração. Novos imports tardios devem preencher disponibilidade real no relógio simulado. O pipeline filtra data econômica e disponibilidade.
- Estorno é integral, vinculado à referência original da mesma conta. O motor não cria operações de estorno: apenas prepara os dados existentes; não há endpoint bancário novo para isso.
- Valores inválidos, não finitos, negativos na entrada ou referências conflitantes falham. Despesas líquidas realizadas podem ser negativas por estorno, mas previsão de despesa variável é não negativa.
- Receitas avulsas, inclusive crédito inicial, não são projetadas como recorrência sem evidência mínima.
- Modelo e baselines são estimativas, sem meta de acurácia aprovada ou incerteza calibrada. Modelos não usam eventos futuros agendados.
- A seed é 42 por padrão; algoritmo de boosting não usa aleatoriedade. Versão identifica algoritmo e hash das amostras; previsão persiste também hash do dataset.
- Testes automatizados validam lógica e integração PostgreSQL; aceite visual em dispositivo continua separado e deve constar como não verificado se não executado.

Evidências e status por task em [IMPLEMENTATION_STATUS](../IMPLEMENTATION_STATUS.md).

## Complemento PO — revisão das TASK-026 a 030

- Um lançamento mensal já realizado, inclusive antecipado, ocupa a competência (descrição normalizada, direção, ano/mês); o próximo evento deve ocorrer no mês seguinte. O histórico disponível, sem estornos, determina essa ocupação. Reverter integralmente o lançamento permite reconsiderar a competência se ainda houver evidência mínima do padrão.
- No treino variável, descartar origens anteriores ao reconhecimento das contas fixas identificadas no corte de treino. Isso impede ensinar essas contas como despesas variáveis e somá-las novamente à projeção fixa. Os atributos e rótulos das origens restantes continuam causais. Sem amostras restantes, manter fallback explícito de histórico insuficiente.
- A prova de cliente não visto deve treinar em um histórico fictício e reutilizar o mesmo modelo, sem chamar `fit`, em outro cliente com referências distintas. Recusar modelo treinado além da data de corte da inferência. O reuso é uma capacidade interna do motor; a API mantém o treino por execução já existente.
- Consultar versões anteriores ao abrir a tela sem criar execução adicional. Falha de consulta deve mostrar erro e permitir nova tentativa; não usar cenário local como substituto.
