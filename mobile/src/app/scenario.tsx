import { useState } from "react";
import { Text, TextInput } from "react-native";
import { useDemo } from "@/demo/DemoProvider";
import {
  currentSnapshot,
  dateLabel,
  money,
  parseCents,
  projection,
} from "@/demo/model";
import { Screen, Card, Button, Chips, Badge } from "@/components/ui";
import { ForecastChart } from "@/components/ForecastChart";
import { ui, theme } from "@/theme";
export default function Scenario() {
  const { state } = useDemo();
  const [value, setValue] = useState("");
  const [amount, setAmount] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [horizon, setHorizon] = useState(7);
  const baseline = currentSnapshot(state).points.slice(0, horizon);
  const scenario =
    amount === null ? [] : projection(state, amount).slice(0, horizon);
  const risk = scenario.find((p) => p.balance < 0);
  return (
    <Screen
      back
      title="E se eu gastar…"
      subtitle="Explore possibilidades sem alterar sua conta ou as previsões salvas."
    >
      <Badge text="Simulação hipotética · nenhum débito" />
      <Text style={ui.label}>Valor do gasto em reais, hoje</Text>
      <TextInput
        accessibilityLabel="Valor do gasto hipotético"
        keyboardType="decimal-pad"
        placeholder="Ex.: 500,00"
        maxLength={10}
        style={ui.input}
        value={value}
        onChangeText={setValue}
      />
      {error !== "" && (
        <Text accessibilityRole="alert" style={{ color: theme.colors.red }}>
          {error}
        </Text>
      )}
      <Chips
        values={[7, 15, 30]}
        value={horizon}
        onChange={setHorizon}
        label={(n) => `${n} dias`}
      />
      <Button
        title="Comparar cenários"
        onPress={() => {
          const parsed = parseCents(value);
          if (parsed === null) {
            setError(
              "Informe um valor maior que zero, sem separador de milhar.",
            );
            return;
          }
          setAmount(parsed);
          setError("");
        }}
      />
      {amount !== null && (
        <Card>
          <Text style={ui.heading}>Impacto de {money(amount)}</Text>
          <ForecastChart
            dates={baseline.map((p) => p.date)}
            series={[
              baseline.map((p) => p.balance),
              scenario.map((p) => p.balance),
            ]}
            labels={["Cenário atual", "Com gasto hipotético"]}
          />
          <Text style={ui.body}>
            Saldo ao final: {money(scenario.at(-1)!.balance)}. Redução de{" "}
            {money(amount)} em relação ao cenário atual.
          </Text>
          <Badge
            text={
              risk
                ? `Saldo negativo em ${dateLabel(risk.date)}`
                : "Sem saldo negativo neste cenário"
            }
            tone={risk ? "amber" : "green"}
          />
          <Text style={ui.body}>
            Resultado ilustrativo, sem intervalo de confiança estimado. Nenhuma
            movimentação ou versão foi salva.
          </Text>
        </Card>
      )}
    </Screen>
  );
}
