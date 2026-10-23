import { useState } from "react";
import { Text, TextInput } from "react-native";
import { useAuth } from "@/auth/AuthProvider";
import { Card, Button, Chips, Badge } from "@/components/ui";
import { ForecastChart } from "@/components/ForecastChart";
import { decimalInput } from "@/features/banking/inputs";
import { formatDecimal } from "@/features/banking/contracts";
import { errorMessage } from "@/services/errors";
import { ui } from "@/theme";
import { simulateForecast } from "./api";
import type { Horizon } from "./contracts";
export function ApiSimulator() {
  const account = useAuth().session?.accounts[0]?.id;
  const [value, setValue] = useState("");
  const [horizon, setHorizon] = useState<Horizon>(7);
  const [result, setResult] = useState<{account: string; data: Awaited<ReturnType<typeof simulateForecast>>} | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  async function simulate() {
    const amount = decimalInput(value);
    if (!amount) {setError("Informe um valor positivo com até duas casas decimais."); return;}
    if (!account || busy) return;
    setBusy(true); setError(null); setResult(null);
    try {setResult({account, data: await simulateForecast(account, amount, horizon)});}
    catch (cause) {setError(errorMessage(cause));}
    finally {setBusy(false);}
  }
  const data = result && result.account === account ? result.data : null;
  return <Card>
    <Text style={ui.heading}>Simular na conta persistida</Text>
    <Badge text="Hipótese sem débito nem alteração do extrato" />
    <TextInput accessibilityLabel="Gasto hipotético pela API" value={value} onChangeText={setValue} keyboardType="decimal-pad" style={ui.input} />
    <Chips values={[7, 15, 30] as Horizon[]} value={horizon} onChange={setHorizon} label={n => `${n} dias`} />
    <Button title={busy ? "Simulando…" : "Calcular impacto pela API"} disabled={busy || !account} onPress={() => void simulate()} />
    {error && <Text accessibilityRole="alert">{error}</Text>}
    {data && <>
      <Text style={ui.body}>Impacto hipotético: {formatDecimal(data.amount)} · data-base {data.after.base_date} · {data.after.horizon} dias</Text>
      <ForecastChart dates={data.after.points.map(p => p.date)} series={[data.before.points.map(p => Number(p.balance) * 100), data.after.points.map(p => Number(p.balance) * 100)]} labels={["Antes", "Gasto hipotético"]} />
      <Text style={ui.body}>{data.after.risk ? `Déficit estimado em ${data.after.risk.date}` : "Sem déficit previsto neste cenário"}. O saldo real e o extrato permanecem inalterados.</Text>
    </>}
  </Card>;
}
