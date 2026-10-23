import { useRef, useState } from "react";
import { router, useLocalSearchParams } from "expo-router";
import { Text, TextInput } from "react-native";
import { useAuth } from "@/auth/AuthProvider";
import { useBalance } from "@/features/banking/useBalance";
import { useCategories } from "@/features/banking/useCategories";
import { decimalInput, idempotencyKey } from "@/features/banking/inputs";
import { bankingUpdated } from "@/features/banking/refresh";
import { formatDecimal, type Receipt } from "@/features/banking/contracts";
import { request } from "@/services/http";
import { errorMessage } from "@/services/errors";
import { Screen, Card, Button, Chips, Badge } from "@/components/ui";
import { ui, theme } from "@/theme";
export default function Movement() {
  const { kind: parameter } = useLocalSearchParams<{ kind?: string }>();
  const kind = parameter === "income" ? "income" : parameter === "expense" ? "expense" : "pix";
  const { session } = useAuth();
  const account = session?.accounts[0]?.id;
  const balance = useBalance();
  const { categories, error: categoryError } = useCategories();
  const [description, setDescription] = useState("");
  const [value, setValue] = useState("");
  const [recipient, setRecipient] = useState("");
  const [category, setCategory] = useState(kind === "income" ? "income" : kind === "pix" ? "pix" : "other");
  const [stage, setStage] = useState<"form" | "review" | "receipt">("form");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const locked = useRef(false);
  const [payload, setPayload] = useState<Record<string, string> | null>(null);
  function review() {
    const amount = decimalInput(value);
    if (!amount || !description.trim() || (kind === "pix" && !recipient.trim())) {
      setError("Informe descrição, valor positivo com até duas casas e favorecido fictício para Pix."); return;
    }
    setPayload({amount, description: description.trim(), category_id: category, idempotency_key: idempotencyKey(),
      ...(kind === "pix" ? {recipient: recipient.trim()} : {})});
    setError(""); setStage("review");
  }
  async function submit() {
    if (locked.current || !payload || !account) return;
    locked.current = true; setBusy(true); setError("");
    try {
      const result = await request<Receipt>(kind === "pix" ? "/pix/simulate" : `/accounts/${account}/${kind === "income" ? "credits" : "debits"}`, {
        method: "POST", data: {...payload, ...(kind === "pix" ? {account_id: account} : {})},
      });
      setReceipt(result); setStage("receipt"); bankingUpdated();
    } catch (cause) { setError(errorMessage(cause)); }
    finally { locked.current = false; setBusy(false); }
  }
  return <Screen back title={stage === "receipt" ? "Comprovante simulado" : kind === "income" ? "Registrar receita" : kind === "expense" ? "Registrar despesa" : "Enviar Pix simulado"}
    subtitle="Conta fictícia persistida · nenhuma transferência real.">
    {stage === "receipt" && receipt ? <>
      <Card><Badge text="Confirmado no servidor · dados fictícios" tone="green" />
        <Text style={ui.amount}>{formatDecimal(receipt.transaction.amount)}</Text>
        <Text style={ui.label}>{receipt.transaction.description}</Text>
        {receipt.transaction.recipient && <Text style={ui.body}>Favorecido fictício: {receipt.transaction.recipient}</Text>}
        <Text style={ui.body}>Data: {receipt.transaction.occurred_on}</Text>
        <Text selectable style={ui.body}>Identificador: {receipt.transaction.id}</Text>
        <Text style={ui.body}>Saldo após consulta: {formatDecimal(receipt.balance)}</Text>
      </Card><Button title="Ver extrato" onPress={() => router.replace("/(tabs)/statement")} />
      <Button secondary title="Voltar ao início" onPress={() => router.replace("/(tabs)")} />
    </> : stage === "review" ? <>
      <Card><Text style={ui.heading}>Confira antes de confirmar</Text>
        <Text style={ui.amount}>{formatDecimal(payload!.amount!)}</Text>
        <Text style={ui.body}>{description}</Text>
        {kind === "pix" && <Text style={ui.body}>Favorecido fictício: {recipient}</Text>}
        <Text style={ui.body}>Saídas acima do saldo são recusadas. Repetir esta solicitação não duplica a movimentação.</Text>
      </Card>
      <Button title={busy ? "Confirmando…" : "Confirmar"} disabled={busy} onPress={() => {void submit();}} />
      {!error && <Button secondary title="Editar antes de enviar" disabled={busy} onPress={() => setStage("form")} />}
      {error && <Text style={ui.body}>Tente novamente com a mesma solicitação. Em dúvida, confira o extrato antes de iniciar outra.</Text>}
    </> : <>
      <Card><Text style={ui.body}>Saldo confirmado: {balance.data ? formatDecimal(balance.data.balance) : balance.loading ? "Consultando…" : "Indisponível"}</Text></Card>
      <Text style={ui.label}>Descrição</Text><TextInput accessibilityLabel="Descrição" value={description} onChangeText={setDescription} maxLength={120} style={ui.input} />
      <Text style={ui.label}>Valor em reais</Text><TextInput accessibilityLabel="Valor em reais" value={value} onChangeText={setValue} keyboardType="decimal-pad" maxLength={19} style={ui.input} placeholder="0,00" />
      {kind === "pix" && <><Text style={ui.label}>Favorecido fictício</Text><TextInput accessibilityLabel="Favorecido fictício" value={recipient} onChangeText={setRecipient} maxLength={120} style={ui.input} placeholder="Ex.: mercado@demo.local" /></>}
      <Text style={ui.label}>Categoria</Text><Chips values={categories.map(c => c.id)} value={category} onChange={setCategory} label={id => categories.find(c => c.id === id)?.name ?? id} />
      <Button title="Revisar movimentação" disabled={!account || !categories.length} onPress={review} />
    </>}
    {(error || categoryError) && <Text accessibilityRole="alert" style={{color: theme.colors.red}}>{error || categoryError}</Text>}
  </Screen>;
}
