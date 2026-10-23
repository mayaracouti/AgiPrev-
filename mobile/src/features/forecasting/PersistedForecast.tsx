import { bankingUpdated } from "@/features/banking/refresh";
import { useEffect, useState } from "react";
import { Text } from "react-native";
import { useAuth } from "@/auth/AuthProvider";
import { Card, Button, Chips } from "@/components/ui";
import { ForecastChart } from "@/components/ForecastChart";
import { ui } from "@/theme";
import { errorMessage } from "@/services/errors";
import { formatDecimal } from "@/features/banking/contracts";
import { dailySeries, forecast, forecasts } from "./api";
import type { ForecastRun, Horizon } from "./contracts";

export function PersistedForecast() {
  const {session} = useAuth();
  const account = session?.accounts[0]?.id;
  const [horizon, setHorizon] = useState<Horizon>(7);
  const [result, setResult] = useState<{account: string; run: ForecastRun} | null>(null);
  const [historyResult, setHistory] = useState<{account: string; rows: ForecastRun[]} | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const history = historyResult && historyResult.account === account ? historyResult.rows : [];
  useEffect(() => {
    if (!account) return;
    let active = true;
    void forecasts(account).then(rows => {
      if (!active) return;
      setHistory(previous => {
        const current = previous?.account === account ? previous.rows : [];
        const merged = new Map([...rows, ...current].map(item => [item.id, item]));
        return {account, rows: [...merged.values()].sort((a, b) => b.created_at.localeCompare(a.created_at))};
      });
      setHistoryError(null);
    }).catch(cause => {if (active) setHistoryError(errorMessage(cause));});
    return () => {active = false;};
  }, [account, retry]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const run = result && result.account === account ? result.run : null;
  async function generate() {
    if (!account || busy) return;
    setBusy(true); setError(null);
    try {
      await dailySeries(account);
      const next = await forecast(account, horizon, "hybrid");
      setResult({account, run: next}); bankingUpdated();
      setHistory(previous => ({account, rows: [next, ...(previous?.account === account ? previous.rows.filter(item => item.id !== next.id) : [])]}));
    } catch (cause) {setError(errorMessage(cause));}
    finally {setBusy(false);}
  }
  return <Card>
    <Text style={ui.heading}>Previsão do histórico persistido</Text>
    <Text style={ui.body}>Estimativa com dados fictícios. Recorrências por heurística e despesas variáveis por modelo treinado; incerteza não calibrada.</Text>
    <Chips values={[7, 15, 30] as Horizon[]} value={horizon} onChange={setHorizon} label={n => `${n} dias`} />
    <Button title={busy ? "Calculando…" : "Gerar previsão pela API"} onPress={() => void generate()} />
    {error && <Text accessibilityRole="alert">{error}</Text>}
    {run && <>
      <Text style={ui.body}>{run.model_version === "hybrid-insufficient-history-v1" ? "Histórico insuficiente para treinar despesas variáveis; componente variável zerado." : run.estimate_notice}</Text>
      <Text style={ui.body}>Data-base {run.base_date} · gerada em {run.created_at} · {run.horizon} dias · versão {run.id} · {run.model_version}</Text>
      {run.experiment_id && <Text selectable style={ui.body}>Experimento {run.experiment_id} · versão {run.experiment_version ?? run.model_version}</Text>}
      <ForecastChart dates={run.points.map(p => p.date)} series={[run.points.map(p => Math.round(Number(p.balance)*100))]} labels={["Saldo estimado pela API"]} />
      <ForecastChart dates={run.points.map(p => p.date)} series={[run.points.map(p => Math.round(Number(p.variable_expense)*100))]} labels={["Despesas variáveis estimadas"]} />
      <Text style={ui.label}>Calendário previsto</Text>
      {run.points.flatMap(p => p.events).map(e => <Text style={ui.body} key={`${e.date}:${e.direction}:${e.description}`}>{e.date} · {e.description} · {formatDecimal(e.amount)} · {e.direction === "credit" ? "receita" : "conta fixa"}</Text>)}
    </>}
      <Text style={ui.label}>Versões preservadas</Text>
      {historyError && <><Text accessibilityRole="alert">{historyError}</Text><Button secondary title="Recarregar versões" onPress={() => setRetry(value => value + 1)} /></>}
      {history.map(item => <Button secondary key={item.id} title={`${item.base_date} · ${item.horizon} dias · ${item.id}`} onPress={() => account && setResult({account, run: item})} />)}
  </Card>;
}
