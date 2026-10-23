# Demonstração guiada do AgiPrevê — 10 minutos

Protótipo demonstrativo não oficial, exclusivamente com dados fictícios. O roteiro é um procedimento reproduzível; sua existência não comprova homologação visual em Android/iOS. Números devem vir das respostas persistidas e dos relatórios calculados, nunca deste roteiro.

## Preparação fora dos 10 minutos

Seguir [desenvolvimento local](local-development.md) para `.env`, Docker e URL do Expo. Preservar credenciais locais e volume existente. Na raiz:

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps -a
docker compose exec api alembic current
docker compose exec api python -m app.modules.simulation.generator --seed 42 --count 6
curl --fail http://localhost:8000/health/ready
cd mobile
npm ci
npm run check
npm start
```

Seed `42`, versão `synthetic-v1`, seis perfis e data inicial sintética `2026-10-23`. Geração idempotente não apaga movimentos existentes. Para repetição financeira exata, usar um ambiente demonstrativo separado sem movimentos manuais anteriores. Não resetar o volume de desenvolvimento. Instalar/abrir Expo no dispositivo e conceder permissões apenas quando solicitado. O perfil `tight` é candidato para risco; verificar a previsão antes de apresentar e não afirmar déficit se a resposta não o indicar.

Na documentação interativa `http://localhost:8000/docs`, autenticar com o cliente fictício retornado pela API e a `DEMO_PASSWORD` configurada. Guardar IDs de conta, previsão e experimento; não copiar token para documentação. Endpoints, corpos e autorização devem seguir o OpenAPI do checkout executado.

## Roteiro cronometrado

| Tempo | Ação e evidência a mostrar |
| --- | --- |
| 0:00–1:00 | Selecionar cliente fictício. Explicar aviso de protótipo e confirmar perfil/data virtual. |
| 1:00–2:00 | Início e Extrato: mostrar saldo confirmado pela API e uma movimentação persistida. Registrar saldo inicial sem arredondamento adicional. |
| 2:00–3:00 | AgiPrevê: gerar horizonte 30 dias. Mostrar data-base, versão do modelo, ID da previsão e último dia. Guardar versão anterior. |
| 3:00–4:00 | Mostrar primeiro déficit previsto, severidade e explicação, se existente. Sem déficit, mostrar explicitamente ausência de risco e mudar para perfil previamente validado somente se necessário. |
| 4:00–5:30 | Executar Pix simulado pelo fluxo persistido, em valor positivo e dentro do saldo disponível. Conferir comprovante, débito no extrato e atualização do saldo. Não usar o cenário visual local neste passo. |
| 5:30–6:30 | Mostrar previsão após Pix e recuperar a versão anterior. Comparar mesmas datas e diferença em reais calculada pelas curvas; registrar os dois IDs. Se recálculo falhar, mostrar estado obsoleto/retry e preservar comprovante. |
| 6:30–7:00 | Abrir central de alertas, detalhe e leitura. Se não houver déficit, ausência de alerta preventivo é o resultado esperado; gasto maior não basta para dispará-lo. |
| 7:00–8:00 | Conta → Área dev: avançar data virtual para uma data dentro do horizonte. Reabrir real × previsto. Futuro permanece sem observado; conferir uma data efetivamente realizada. |
| 8:00–9:30 | Abrir relatório calculado e comparar modelos, horizontes e perfis. Exibir MAE, MSE, RMSE, Bias, Precision, Recall, F1 e lead time, com dataset, seed e experimento. Métrica indefinida por ausência de eventos deve aparecer como indisponível, não como sucesso. |
| 9:30–10:00 | Mostrar limitações dos dados sintéticos, distinção de validação/holdout e encerramento sem promessa financeira ou oferta de crédito. |

## Evidências e checklist

- [ ] API e PostgreSQL saudáveis; migração atual aplicada; app conecta sem fallback de saldo.
- [ ] Cliente, perfil, seed, data virtual e IDs anotados no registro da sessão.
- [ ] Valores de saldo e Pix conferidos no extrato; previsão anterior continua consultável.
- [ ] Risco/alerta mostrado corresponde ao retorno real; não foi inventado para a narrativa.
- [ ] Avanço virtual não converte datas futuras em observado antes de sua realização.
- [ ] Métricas exibidas provêm de avaliação executada e identificam conjunto/partição e modelo.
- [ ] Notificação local testada em dispositivo, ou explicitamente marcada não verificada.
- [ ] Renderização, navegação e acessibilidade verificados em dispositivo, ou marcados não verificados.

O relatório final de aceite deve registrar resultados e bloqueios dessa sessão. Este checklist vazio não representa execução.

## Repetir cenários e medição CPU

```bash
docker compose -f compose.test.yaml run --rm tests pytest -p no:cacheprovider tests/test_financial_scenarios.py -q
docker compose exec api python -m app.modules.forecasting.benchmark --count 1000 --seed 42 --output /tmp/agipreve-performance.json
```

O benchmark mede projeção e recálculo sequenciais de 1000 clientes sintéticos, com treinamento único separado. Não mede HTTP, PostgreSQL, filas, renderização ou treinamento por cliente. Seu P95 não substitui latência ponta a ponta nem teste concorrente. Copiar o JSON de dentro do container para guardar a evidência. A avaliação holdout final não deve ser repetida para selecionar modelos: recuperar o experimento já registrado.

## Contratos da demonstração

Todos os caminhos abaixo têm prefixo `/api/v1/accounts/{account_id}` e exigem sessão da própria conta:

- `GET /forecasts/latest`: dashboard agregado da última previsão.
- `GET /forecasts/{run_id}/series`: observado realizado e previsto da versão escolhida.
- `POST /forecasts/simulate`: gasto hipotético com `amount` decimal string e `horizon`; não cria transação.
- `GET /alerts`, `GET /alerts/{alert_id}` e `PATCH /alerts/{alert_id}` com `{"read":true}`.
- `POST /experiments`, `GET /experiments` e `GET /evaluation/reports?format=json` (também CSV/HTML e filtros disponibilizados no OpenAPI).

O comprovante do Pix informa `forecast_id`, `previous_forecast_id`, `forecast_status` e `correlation_id`. Após avançar a data, gerar manualmente nova previsão se necessário; avanço não deve ser apresentado como recálculo automático sem confirmação do retorno.

## Evidência medida — 23/10/2026

Executados os 18 cenários em `tests/test_financial_scenarios.py`: **18 passed** (0,31 s), com um aviso de depreciação Starlette/httpx. Os identificadores abaixo são um mapeamento adotado nesta implementação, pois não havia catálogo CT existente; não representam casos originais recuperados de documentação.

| Caso | Invariante financeiro |
| --- | --- |
| CT-001 | Saldo positivo sem risco |
| CT-002 | Déficit com data e saldo exatos |
| CT-003 | Saldo zero sem déficit |
| CT-004 | Salário: data e valor |
| CT-005 | Aluguel sem dupla contagem variável |
| CT-006 | Recorrência em mês curto |
| CT-007 | Futuro excluído do corte |
| CT-008 | Disponibilidade tardia excluída |
| CT-009 | Duplicata idêntica idempotente |
| CT-010 | Duplicata conflitante rejeitada |
| CT-011 | Estorno restaura saldo |
| CT-012 | Estorno órfão rejeitado |
| CT-013 | Lacunas diárias zeradas |
| CT-014 | Dinheiro inválido rejeitado |
| CT-015 | Atributos causais |
| CT-016 | Modelo determinístico com atributos não vistos e saída não negativa |
| CT-017 | Identidade de saldo em 7/15/30 dias |
| CT-018 | Baselines determinísticos e horizonte inválido rejeitado |

Benchmark real em container Python 3.12.15, Linux 6.14.0-37 x86_64, 16 CPUs lógicas visíveis, seed42, 1000 clientes distintos, 30 dias: treinamento único **0,540 s**; inferência P95 **0,016052 s**, máximo **0,049866 s**; recálculo P95 **0,016236 s**, máximo **0,058260 s**. Tempos acumulados: 13,009 s e 13,105 s; 30000 pontos de recálculo gerados. Evidência bruta: `/tmp/agipreve-performance.json` no workspace da execução. O ambiente compartilhado e a carga concorrente não foram controlados; os números caracterizam apenas esse ensaio CPU sequencial. Não aprovam desempenho HTTP/E2E nem renderização em dispositivo (não verificados).

## Preparação determinística do risco (comando preferido)

Para não depender de um perfil apenas chamado `tight`, preparar seis clientes em uma seed dedicada:

```bash
docker compose exec api python -m app.demo --seed 4241
```

O comando gera os seis perfis com a senha fictícia do ambiente, escolhe o índice 2 e registra uma despesa **fictícia** calculada para deixar R$ 50,00. O valor da despesa vem do ledger, não é um saldo sobrescrito. Gera previsão/alerta pelo mesmo fluxo persistido das operações e imprime o dashboard com IDs e risco calculado. Reexecutar a seed preserva movimentos e relógio; para uma demonstração nova, escolher outra seed, sem apagar dados.

Selecionar `synthetic-4241-2@demo.local` e usar a senha fictícia configurada. Depois da previsão inicial de 30 dias, um Pix fictício de R$ 10,00, dentro do saldo, permite mostrar as duas versões e a diferença efetivamente calculada. Se a conta já tiver sido usada e o saldo não permitir, preparar outra seed; não afirmar que o comando restaura o saldo.

Relatório técnico: em `/docs`, executar POST `/accounts/{id}/experiments` com `train_end=2026-07-01`, `validation_end=2026-08-01`, `final_end=2026-09-01`, `seed=42`; recuperar via GET `/experiments` e `/evaluation/reports?format=html`. A seed42 desse corpo é a seed do algoritmo determinístico, enquanto 4241 identifica os dados gerados. O HTML autenticado oferece filtros de modelo, horizonte, perfil e partição. Para abrir fora do Swagger, salvar a resposta autorizada como HTML local; não colocar token na URL. O holdout já registrado é reutilizado: não alterar a seleção depois de ver seus resultados.

As métricas desse período podem ser indefinidas por ausência de déficit no holdout, mesmo que o orçamento preparado na data atual tenha risco. A preparação atual não muda o holdout passado nem transforma uma métrica indefinida em resultado aprovado.
