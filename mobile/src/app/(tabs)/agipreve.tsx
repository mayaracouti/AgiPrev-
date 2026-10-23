import { FinancialDashboard } from "@/features/forecasting/FinancialDashboard";
import { PersistedForecast } from "@/features/forecasting/PersistedForecast";
import { RecurrencesCard } from "@/features/banking/components/RecurrencesCard";
import { useState } from "react";
import { router } from "expo-router";
import { Text, View } from "react-native";
import { useDemo } from "@/demo/DemoProvider";
import {
  currentSnapshot,
  dateLabel,
  money,
  realizedBalance,
} from "@/demo/model";
import { Screen, Card, Chips, Section, Badge, Button } from "@/components/ui";
import { ForecastChart } from "@/components/ForecastChart";
import { ui, theme } from "@/theme";
export default function Forecast() {
  const { state, balance } = useDemo();
  const [horizon, setHorizon] = useState(7);
  const current = currentSnapshot(state);
  const previous = state.snapshots.at(-2);
  const points = current.points.slice(0, horizon);
  const risk = points.find((p) => p.balance < 0);
  const income = points.reduce((sum, p) => sum + p.income, 0);
  const expense = points.reduce((sum, p) => sum + p.expense, 0);
  const comparison = state.snapshots.find((s) =>
    s.points.some((p) => p.date <= state.date),
  );
  const matured = comparison?.points.filter((p) => p.date <= state.date) ?? [];
  const accumulated = points.map((_, index) =>
    points.slice(0, index + 1).reduce((sum, p) => sum + p.expense, 0),
  );
  return (
    <Screen
      title="AgiPrevê"
      subtitle="Uma visão clara para você decidir melhor."
    >
      <FinancialDashboard />
      <PersistedForecast />
      <RecurrencesCard />
      <Card>
        <Badge
          text={
            risk ? "Atenção ao saldo projetado" : "Saldo positivo no cenário"
          }
          tone={risk ? "amber" : "green"}
        />
        <Text style={ui.body}>
          {risk
            ? `O primeiro saldo negativo do cenário aparece em ${dateLabel(risk.date)}: ${money(risk.balance)}.`
            : `Neste cenário, seu saldo permanece positivo pelos próximos ${horizon} dias.`}
        </Text>
        <Text style={ui.body}>
          Projeção ilustrativa baseada em regras fixas de demonstração. Não é
          uma garantia nem uma avaliação financeira validada.
        </Text>
      </Card>
      <Section
        title="Previsão do seu saldo"
        action="Versões"
        onPress={() => router.push("/versions")}
      />
      <Chips
        values={[7, 15, 30]}
        value={horizon}
        onChange={setHorizon}
        label={(n) => `${n} dias`}
      />
      <Card>
        <Text style={ui.body}>
          {dateLabel(points.at(-1)!.date)} · saldo estimado
        </Text>
        <Text
          style={[
            ui.amount,
            { color: risk ? theme.colors.amber : theme.colors.text },
          ]}
        >
          {money(points.at(-1)!.balance)}
        </Text>
        <ForecastChart
          dates={points.map((p) => p.date)}
          series={[points.map((p) => p.balance)]}
          labels={["Previsto · cenário local"]}
        />
        <Text style={[ui.body, { fontSize: 11 }]}>
          Gerada em {dateLabel(current.simulatedDate)} às 12h (relógio simulado)
          · {current.id} · horizonte armazenado: 30 dias
        </Text>
        <Text style={[ui.body, { fontSize: 11 }]}>
          {current.model} · saldo de referência{" "}
          {money(current.referenceBalance)}
        </Text>
      </Card>
      <View style={ui.grid}>
        <Card style={{ flex: 1, minWidth: 130 }}>
          <Text style={ui.body}>Receitas previstas</Text>
          <Text style={[ui.label, { color: theme.colors.green }]}>
            {money(income)}
          </Text>
        </Card>
        <Card style={{ flex: 1, minWidth: 130 }}>
          <Text style={ui.body}>Despesas previstas</Text>
          <Text style={ui.label}>{money(expense)}</Text>
        </Card>
      </View>
      <Section title="O que mudou na previsão" />
      <Card>
        {previous ? (
          <>
            <Text style={ui.label}>{current.reason}</Text>
            <Text style={ui.body}>
              Saldo de referência anterior: {money(previous.referenceBalance)}.
              Atual: {money(balance)}.
            </Text>
            <Text style={ui.body}>
              Mudança na referência:{" "}
              {money(current.referenceBalance - previous.referenceBalance)}. A
              nova versão usa o saldo confirmado; a versão {previous.id}{" "}
              permanece inalterada.
            </Text>
            <Button
              secondary
              title="Comparar versões e fatores"
              onPress={() => router.push("/versions")}
            />
          </>
        ) : (
          <Text style={ui.body}>
            Registre uma movimentação no início para ver como ela altera o saldo
            e gera uma nova versão do cenário.
          </Text>
        )}
      </Card>
      <Section title="Real × previsto" />
      <Card>
        <Text style={ui.body}>
          Comparamos somente datas já realizadas com uma previsão criada
          anteriormente. Nenhum valor futuro é apresentado como observado.
        </Text>
        {matured.length ? (
          <>
            <Badge text={`Referência: ${comparison!.id}`} />
            <ForecastChart
              dates={matured.map((p) => p.date)}
              series={[
                matured.map((p) => p.balance),
                matured.map((p) => realizedBalance(state, p.date)!),
              ]}
              labels={["Previsto anteriormente", "Realizado sintético"]}
            />
            <Text style={ui.body}>
              Desvio no último dia:{" "}
              {money(
                realizedBalance(state, matured.at(-1)!.date)! -
                  matured.at(-1)!.balance,
              )}
            </Text>
          </>
        ) : (
          <Button
            secondary
            title="Avançar o relógio simulado"
            onPress={() => router.push("/account")}
          />
        )}
      </Card>
      <Section title="Despesas acumuladas" />
      <Card>
        <ForecastChart
          dates={points.map((p) => p.date)}
          series={[accumulated]}
          labels={["Acumulado previsto"]}
        />
      </Card>
      <Section title="Padrões do cenário" />
      <Card>
        <Text style={ui.label}>Receitas e contas recorrentes</Text>
        <Text style={ui.body}>
          O cenário inclui salário no dia 5, aluguel no dia 8 e cobranças de R$
          420,00 no dia 28. A despesa cotidiana prevista é R$ 45,00/dia. São
          premissas fictícias configuradas, não recorrências detectadas por um
          algoritmo.
        </Text>
      </Card>
      <Section title="Recomendação demonstrativa" />
      <Card style={{ backgroundColor: "#EAF1FF" }}>
        <Text style={ui.label}>
          {risk
            ? "Revise os gastos antes de confirmar"
            : "Construa uma margem de tranquilidade"}
        </Text>
        <Text style={ui.body}>
          {risk
            ? "Compare o impacto de um gasto hipotético e observe quais dias exigem atenção. Os resultados são cenários, não promessas."
            : "Experimente reservar uma margem no seu planejamento e acompanhe as despesas recorrentes."}
        </Text>
        <Button
          secondary
          title="Simular um gasto"
          onPress={() => router.push("/scenario")}
        />
      </Card>
      <Button
        title="Ver alertas preventivos"
        onPress={() => router.push("/alerts")}
      />
    </Screen>
  );
}
