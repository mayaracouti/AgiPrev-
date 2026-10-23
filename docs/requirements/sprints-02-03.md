# TASK-011 a TASK-020 — banco simulado e dados sintéticos

Autorização: solicitação atual substitui a limitação anterior às TASK-001–010. Preservar contratos existentes e cenários locais separados. Personas PO, DEV e QA aplicadas sequencialmente, sem subagentes.

## Regras de aceite

| Task | Entradas e dependências | Saída e critério verificável |
| --- | --- | --- |
| 011 | Conta autenticada, ledger existente | Transaction reutiliza o ledger (uma única fonte de saldo); paginação por cursor estável, data decrescente + UUID; filtros de período, categoria, direção e descrição; sem IDs repetidos entre páginas. |
| 012 | Conta, valor decimal positivo, descrição, chave idempotente | Crédito atômico; repetição idêntica devolve mesmo comprovante; chave com payload diferente retorna 409. |
| 013 | Mesmas entradas, categoria | Débito manual sem cheque especial: saldo insuficiente retorna 409 sem lançamento. Serializar escritas por bloqueio da conta. |
| 014 | Valor, favorecido fictício, chave idempotente | Pix de saída exclusivamente simulado; confirmação e comprovante persistidos na mesma transação do débito. Sem integração externa. |
| 015 | Catálogo fixo de categorias | Categoria com FK em todos os lançamentos, inclusive antigos; classificação padrão por tipo e edição autorizada somente da categoria. |
| 016 | Cenário da conta, data destino | Data monotônica; eventos futuros separados do ledger; avanço materializa cada evento uma vez, sem alterar lançamentos anteriores. |
| 017 | Seed, quantidade (padrão 1000), seis perfis | Gerador versionado e reproduzível; IDs e atributos financeiros determinísticos; senhas com salt aleatório ficam fora da comparação de dados sintéticos. Seletor consulta API e filtra perfis. |
| 018 | Gerador, 12 meses anteriores à data do cenário | Mais de 100 mil lançamentos para 1000 clientes, inseridos em lotes; totais por conta reconciliados com o ledger. Dados e descrições inteiramente fictícios. |
| 019 | Área dev, chave idempotente, atraso salarial/compra/receita | Agenda eventos futuros reproduzíveis; atraso move somente salário pendente; compras/receitas não afetam saldo confirmado antes do avanço. Sem reescrever histórico. |
| 020 | Somente transações realizadas até a data do cenário | Heurística explícita de periodicidade mensal, tolerância ±3 dias e ±10% do valor; mínimo 3 ocorrências; indicador de regularidade, sem alegar probabilidade calibrada ou modelo treinado. Precision/recall efetivamente calculados em cenários rotulados. |

## Casos-limite e limites

Valores REST são strings decimais com duas casas, nunca floats. Recusar zero, negativos, excesso de precisão, UUIDs, datas e categorias inválidos. Conta alheia continua 404. Cursores e filtros inválidos retornam 422. Banco limpo e upgrade sobre dados antigos devem funcionar. Retries concorrentes não podem duplicar débitos nem ultrapassar saldo. Eventos sintéticos podem levar o saldo abaixo de zero para representar risco, política distinta de pagamentos manuais e explicitada na área dev. O relógio não altera o relógio do sistema.

Geração é comando administrativo local, não endpoint público nem rotina automática do startup. Reexecução da mesma seed não duplica clientes/eventos; conflitos com dados alterados devem ser evitados sem sobrescrever histórico. Não criar motor de previsão, push, integração Pix real ou laboratório no app neste lote. Testes objetivos com PostgreSQL real, regressão mobile e medição de recorrências; execução visual nativa permanece separada das evidências automatizadas.
