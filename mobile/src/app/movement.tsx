import { useRef, useState } from "react";
import { router, useLocalSearchParams } from "expo-router";
import {
  Text,
  TextInput,
  View,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useDemo } from "@/demo/DemoProvider";
import { dateLabel, money, parseCents, currentSnapshot } from "@/demo/model";
import { categories, type Category, type TransactionKind } from "@/demo/types";
import { Screen, Card, Button, Chips, Badge } from "@/components/ui";
import { ui, theme } from "@/theme";
export default function Movement() {
  const params = useLocalSearchParams<{ kind?: string }>();
  const kind: TransactionKind =
    params.kind === "income"
      ? "income"
      : params.kind === "expense"
        ? "expense"
        : "pix";
  const { state, balance, confirm } = useDemo();
  const [description, setDescription] = useState("");
  const [value, setValue] = useState("");
  const [category, setCategory] = useState<Category>(
    kind === "income" ? "Renda" : kind === "pix" ? "Pix" : "Outros",
  );
  const [error, setError] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const locked = useRef(false);
  const id = useRef(
    `manual-${Date.now()}-${Math.random().toString(36).slice(2)}`,
  );
  const previous = useRef(currentSnapshot(state));
  const cents = parseCents(value);
  function submit() {
    if (locked.current) return;
    if (cents === null) {
      setError(
        "Use um valor maior que zero, como 120,50, sem separador de milhar.",
      );
      return;
    }
    const message = confirm({
      id: id.current,
      date: state.date,
      description: description.trim(),
      category,
      kind,
      cents,
    });
    if (message) {
      setError(message);
      return;
    }
    locked.current = true;
    setConfirmed(true);
  }
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <Screen
        back
        title={
          confirmed
            ? "Tudo certo!"
            : kind === "income"
              ? "Registrar receita"
              : kind === "expense"
                ? "Registrar despesa"
                : "Enviar Pix"
        }
        subtitle="Simulação visual local · não grava lançamentos no servidor."
      >
        {confirmed ? (
          <>
            <Card style={{ backgroundColor: theme.colors.paleGreen }}>
              <Badge text="Simulação confirmada nesta sessão" tone="green" />
              <Text style={ui.amount}>{money(cents!)}</Text>
              <Text style={ui.label}>{description}</Text>
              <Text style={ui.body}>Saldo do cenário atualizado: {money(balance)}</Text>
            </Card>
            <Card>
              <Text style={ui.heading}>Sua previsão também mudou</Text>
              <Text style={ui.body}>
                Cenário anterior: {previous.current.id} ·{" "}
                {money(previous.current.points[6]!.balance)} em 7 dias
              </Text>
              <Text style={ui.body}>
                Novo cenário: {currentSnapshot(state).id} ·{" "}
                {money(currentSnapshot(state).points[6]!.balance)} em 7 dias
              </Text>
              <Text style={ui.body}>
                A versão anterior foi preservada para comparação. Valores
                ilustrativos, sem inferência de um modelo treinado.
              </Text>
            </Card>
            <Button
              title="Ver impacto no AgiPrevê"
              onPress={() => router.replace("/(tabs)/agipreve")}
            />
            <Button
              secondary
              title="Voltar ao início"
              onPress={() => router.replace("/(tabs)")}
            />
          </>
        ) : (
          <>
            <Card>
              <View style={ui.between}>
                <Text style={ui.body}>Saldo disponível no cenário local</Text>
                <Text style={ui.label}>{money(balance)}</Text>
              </View>
              <Text style={ui.body}>
                Data simulada: {dateLabel(state.date)}
              </Text>
            </Card>
            <Text nativeID="description-label" style={ui.label}>
              {kind === "pix"
                ? "Chave Pix ou favorecido fictício"
                : "Descrição"}
            </Text>
            <TextInput
              accessibilityLabel={
                kind === "pix"
                  ? "Chave Pix ou favorecido fictício"
                  : "Descrição"
              }
              style={ui.input}
              value={description}
              onChangeText={setDescription}
              maxLength={120}
              autoCapitalize="sentences"
              placeholder={
                kind === "pix"
                  ? "Ex.: mercado@exemplo.com"
                  : "Ex.: Compra no mercado"
              }
            />
            <Text style={ui.label}>Valor em reais</Text>
            <TextInput
              accessibilityLabel="Valor em reais"
              style={ui.input}
              keyboardType="decimal-pad"
              value={value}
              onChangeText={setValue}
              placeholder="0,00"
              maxLength={10}
            />
            {kind !== "pix" && (
              <>
                <Text style={ui.label}>Categoria</Text>
                <Chips
                  values={categories}
                  value={category}
                  onChange={setCategory}
                />
              </>
            )}
            {error !== "" && (
              <Text
                accessibilityRole="alert"
                style={{ color: theme.colors.red }}
              >
                {error}
              </Text>
            )}
            <Card>
              <Text style={ui.body}>
                Após confirmar, o saldo e o cenário ilustrativo serão
                atualizados. Nesta demonstração, saídas acima do saldo são
                recusadas. Os dados são apagados ao reiniciar a sessão.
              </Text>
            </Card>
            <Button
              title={
                kind === "pix"
                  ? "Confirmar Pix simulado"
                  : "Confirmar movimentação"
              }
              disabled={!description.trim() || !value}
              onPress={submit}
            />
          </>
        )}
      </Screen>
    </KeyboardAvoidingView>
  );
}
