import { useMemo, useState } from "react";
import { Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { useDemo } from "@/demo/DemoProvider";
import { addDays, money } from "@/demo/model";
import { categories } from "@/demo/types";
import { Screen, Card, Chips, Empty, Button } from "@/components/ui";
import { TransactionRow } from "@/components/TransactionRow";
import { ui } from "@/theme";
export default function Transactions() {
  const { state } = useDemo();
  const [period, setPeriod] = useState(30);
  const [category, setCategory] = useState("Todas");
  const [query, setQuery] = useState("");
  const transactions = useMemo(
    () =>
      [...state.transactions]
        .reverse()
        .filter(
          (tx) =>
            tx.date >= addDays(state.date, 1 - period) &&
            tx.date <= state.date &&
            (category === "Todas" || tx.category === category) &&
            tx.description
              .toLocaleLowerCase("pt-BR")
              .includes(query.toLocaleLowerCase("pt-BR")),
        ),
    [state, period, category, query],
  );
  const income = transactions
    .filter((t) => t.kind === "income")
    .reduce((sum, t) => sum + t.cents, 0);
  const expense = transactions
    .filter((t) => t.kind !== "income")
    .reduce((sum, t) => sum + t.cents, 0);
  return (
    <Screen
      back
      title="Histórico do cenário visual"
      subtitle="Dados locais ilustrativos; não são lançamentos confirmados no servidor."
    >
      <Chips
        values={[7, 15, 30, 90]}
        value={period}
        onChange={setPeriod}
        label={(n) => `${n} dias`}
      />
      <Chips
        values={["Todas", ...categories]}
        value={category}
        onChange={setCategory}
      />
      <TextInput
        accessibilityLabel="Buscar movimentação por descrição"
        style={ui.input}
        value={query}
        onChangeText={setQuery}
        placeholder="Buscar por descrição"
      />
      <Card>
        <View style={ui.between}>
          <View style={{ flex: 1 }}>
            <Text style={ui.body}>Entradas no filtro</Text>
            <Text style={ui.label}>{money(income)}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={ui.body}>Saídas no filtro</Text>
            <Text style={ui.label}>{money(expense)}</Text>
          </View>
        </View>
        <Text style={ui.body}>
          {transactions.length} movimentações encontradas
        </Text>
      </Card>
      {transactions.length ? (
        <Card>
          {transactions.map((tx) => (
            <TransactionRow key={tx.id} item={tx} />
          ))}
        </Card>
      ) : (
        <Empty text="Nenhuma movimentação para esses filtros. Experimente outro período ou categoria." />
      )}
      <Button
        title="Nova movimentação"
        onPress={() => router.push("/movement?kind=expense")}
      />
    </Screen>
  );
}
