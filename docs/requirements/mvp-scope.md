# Escopo do AgiPrevê

## Contexto confirmado

Aplicativo mobile demonstrativo de inteligência financeira preventiva inspirado na proposta AgiPrevê para o Agibank. Deve antecipar o risco de o cliente ficar sem dinheiro antes do fim do mês. Todos os dados são fictícios, sem integração com APIs reais do Agibank. A interface deve exibir “protótipo demonstrativo não oficial, com dados fictícios”.

## Módulos previstos para o MVP

- Banco simulado: consulta de saldo, histórico de transações, recebimentos, despesas, pagamentos Pix simulados e atualização do saldo após movimentações.
- AgiPrevê: análise do histórico, identificação de receitas e despesas recorrentes, projeção da evolução do saldo, comparação entre saldos observados e previsões anteriores, detecção de insuficiência financeira, recálculo após novas transações, alertas preventivos e recomendações contextualizadas.

O fluxo principal da futura demonstração é realizar uma transação simulada e observar a atualização automática da previsão financeira.

## Frontend autorizado

A referência visual está em `/home/mayara/Downloads/projeto/project-bolt-sb1-xykqmzkb/project`. Preservar a linguagem de gradientes azuis, cartões claros, atalhos circulares e navegação inferior, adaptando a referência à stack e à API FastAPI futura. Não reutilizar credenciais, configuração Supabase ou serviços externos da referência.

A entrega atual é um frontend interativo com dados locais em memória. O backend, o motor preditivo real, a autenticação segura, a persistência, o envio de push e o executor de backtesting serão desenvolvidos em etapas posteriores. Os exemplos antigos de login não originaram requisitos; a seleção de usuários fictícios passa a existir por autorização explícita do RF-001 nesta etapa.

## Cobertura dos requisitos funcionais na interface

| Requisitos | Representação atual | Integração futura |
| --- | --- | --- |
| RF-001 | Seleção de perfil fictício e sessão demonstrativa | Autenticação, autorização e sessões seguras |
| RF-002 a RF-006 | Saldo, extrato, receitas, despesas e Pix em memória; atualização compartilhada | Persistência e transação atômica no servidor |
| RF-007 | Históricos sintéticos reproduzíveis por perfil e semente | Geração versionada no backend |
| RF-008 | Filtros por período, categoria e descrição | Consulta paginada na API |
| RF-009 | Avanço de 1 ou 7 dias no relógio simulado | Relógio e eventos persistidos |
| RF-010 | Validação de formulário, centavos inteiros, bloqueio de confirmação repetida e saldo insuficiente | Idempotência e concorrência no servidor |
| RF-011 a RF-015 | Histórico visível, categorias selecionadas e calendário fictício de receitas/despesas explicado | Análise e detecção de recorrências reais; classificação automática |
| RF-016 e RF-017 | Cenários de 7, 15 e 30 dias com primeira data e valor negativo | Projeções do motor validado |
| RF-018 a RF-020 | Comparação em datas realizadas, nova versão após movimentações e metadados preservados na sessão | Versões imutáveis no banco |
| RF-021 | Não apresentar intervalo de confiança sem estimativa | Intervalos calculados e calibrados |
| RF-022 a RF-025 | Desvio em reais, risco por saldo negativo, fatores das regras; comparação de modelos reservada ao ambiente técnico | Limiares, risco estimado e explicabilidade do modelo; comparação executada |
| RF-026 a RF-029 | Alertas internos de risco com motivo, data e déficit; recomendação demonstrativa | Entrega de notificações, limites de despesas e recomendações do motor |
| RF-030 e RF-031 | Gráficos real × previsto e despesas acumuladas | Séries retornadas pela API |
| RF-032 e RF-033 | Cenário hipotético sem débito e impacto de transação na previsão | Simulador e recálculo no servidor |
| RF-034 e RF-035 | Histórico de alertas com resultado sintético posterior e preferência de destaque | Persistência e preferências de notificações do dispositivo |
| RF-036 a RF-040 | Sem tela no aplicativo; estrutura técnica de configuração preparada, sem resultados calculados | Backtesting e métricas efetivamente calculados |
| RF-041 e RF-042 | Sem medição de p95 ou relatório executado; sem tela no aplicativo | Medições e relatórios de avaliação executada |
| RF-043 a RF-045 | Estrutura técnica de parâmetros e versão de dataset, sem tela no aplicativo | Avaliação por perfil, degradação e registro persistente de execuções/modelos |

RF-012 é tratado como P0 conforme a lista de requisitos, mesmo com a detecção de recorrência aparecendo como P1 no resumo inicial de features. As demais prioridades permanecem as fornecidas pelo usuário. Esta tabela não declara o MVP completo: distingue claramente interface, demonstração local e funcionalidades do backend pendentes.

## Requisitos não funcionais

As metas são propostas para o protótipo e precisam de validação:

- RNF-001: recálculo em até 2 segundos no percentil 95; ainda não medido.
- RNF-002: 99% de disponibilidade durante a demonstração; ainda não medido.
- RNF-003: saldo consistente com movimentações confirmadas.
- RNF-004: autenticação, sessões e acesso protegidos; o seletor demonstrativo não atende à segurança de uma autenticação real.
- RNF-005: somente dados fictícios/sintéticos.
- RNF-006: separar banco, predição e notificações.
- RNF-007: suportar 1.000 clientes simulados; ainda não submetido a carga.
- RNF-008: registrar logs, erros, tempos e versões no backend futuro.
- RNF-009: sementes e dados versionados para reprodutibilidade.
- RNF-010: informar motivos de alertas e alterações das previsões.
- RNF-011: evitar transações duplicadas e perda de eventos; garantias duráveis dependem do servidor.
- RNF-012: linguagem acessível e adequada ao risco financeiro.
- RNF-013: módulos desacoplados e testes automatizados.
- RNF-014: qualidade preditiva definida e validada em conjuntos próprios; nenhum resultado apresentado como aprovado nesta etapa.
- RNF-015: impedir uso de dados futuros no treino/inferência; a interface só mostra realizados até a data simulada e preserva previsões anteriores.
- RNF-016: previsões são estimativas, nunca garantias.

A organização técnica está em [estrutura do projeto](../architecture/project-structure.md); execução e roteiro de demonstração estão no [guia de desenvolvimento](../guides/local-development.md).

O Laboratório de avaliação não é uma aba da aplicação bancária. Sua interface e execução serão tratadas em um ambiente técnico separado. Na etapa atual (TASK-007), a navegação contém Início, Extrato, Pix e AgiPrevê; Conta é um fluxo auxiliar.

## Atualização — Sprints 1 e 2

O [refinamento das TASK-001 a TASK-010](sprints-01-02.md) substitui as descrições históricas de integração futura para clientes, contas, autenticação fictícia e saldo. Esses fluxos usam a API FastAPI e PostgreSQL. Cenários, movimentações/Pix visuais e previsões locais continuam demonstrativos, separados do ledger persistido. Consulte as [evidências de implementação](../IMPLEMENTATION_STATUS.md).


## Atualização — banco simulado e dados sintéticos

As [TASK-011 a TASK-020](sprints-02-03.md) autorizam transações e Pix simulados persistidos, categorias, relógio/eventos no servidor, geração de seis perfis e histórico sintético, além de detecção heurística de recorrências. Esses recursos substituem a indicação histórica de integração futura para RF-003–RF-015 no escopo deste lote. Gráficos e previsões do cenário visual anterior continuam locais e identificados; não há motor preditivo treinado ou push nesta entrega.
