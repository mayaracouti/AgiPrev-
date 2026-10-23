import { useState } from "react";
import { Text, View } from "react-native";
import { useDemo } from "@/demo/DemoProvider";
import { currentSnapshot, dateLabel, money } from "@/demo/model";
import { Screen, Card, Chips, Badge } from "@/components/ui";
import { ForecastChart } from "@/components/ForecastChart";
import { ui } from "@/theme";
export default function Versions() {
  const { state } = useDemo();
  const latest = currentSnapshot(state);
  const [selected, setSelected] = useState(
    state.snapshots.at(-2)?.id ?? latest.id,
  );
  const baseline = state.snapshots.find((s) => s.id === selected) ?? latest;
  const aligned = latest.points.filter((p) =>
    baseline.points.some((old) => old.date === p.date),
  );
  return (
    <Screen
      back
      title="Histórico de previsões"
      subtitle="Cada versão preserva a informação disponível na sua data de geração."
    >
      <Chips
        values={state.snapshots.map((s) => s.id)}
        value={selected}
        onChange={setSelected}
      />
      <Card>
        <Badge text={`${baseline.id} · ${baseline.model}`} />
        <Text style={ui.heading}>{baseline.reason}</Text>
        <Text style={ui.body}>
          Gerada: {dateLabel(baseline.simulatedDate)} · horário simulado 12h UTC
        </Text>
        <Text style={ui.body}>
          Horizonte: {baseline.horizon} dias · saldo de referência:{" "}
          {money(baseline.referenceBalance)}
        </Text>
        <Text style={ui.body}>
          Válida como registro ilustrativo desta sessão, sem persistência no
          servidor.
        </Text>
      </Card>
      <Card>
        <Text style={ui.heading}>Comparação com {latest.id}</Text>
        {aligned.length ? (
          <ForecastChart
            dates={aligned.map((p) => p.date)}
            series={[
              aligned.map(
                (p) =>
                  baseline.points.find((old) => old.date === p.date)!.balance,
              ),
              aligned.map((p) => p.balance),
            ]}
            labels={[`${baseline.id} · selecionada`, `${latest.id} · atual`]}
          />
        ) : (
          <Text style={ui.body}>
            Essas versões não possuem datas em comum. Selecione uma versão mais
            recente.
          </Text>
        )}
        <Text style={ui.body}>
          As curvas usam as mesmas datas de calendário; dias fora do horizonte
          compartilhado não entram na comparação.
        </Text>
      </Card>
      <Card>
        <Text style={ui.heading}>Fatores do cenário atual</Text>
        <Text style={ui.body}>
          • Saldo confirmado: {money(latest.referenceBalance)}
        </Text>
        <Text style={ui.body}>
          • Despesas cotidianas previstas: R$ 45,00 por dia
        </Text>
        <Text style={ui.body}>• Calendário fictício de salário e contas</Text>
        <Text style={ui.body}>• Última alteração: {latest.reason}</Text>
        <Text style={ui.body}>
          Estes são fatores das regras locais de demonstração. A explicabilidade
          do modelo real será integrada ao backend.
        </Text>
      </Card>
      <Card>
        <Text style={ui.heading}>Pontos da versão selecionada</Text>
        {baseline.points.map((p) => (
          <View key={p.date} style={ui.between}>
            <Text style={ui.body}>{dateLabel(p.date)}</Text>
            <Text style={ui.label}>{money(p.balance)}</Text>
          </View>
        ))}
      </Card>
    </Screen>
  );
}
