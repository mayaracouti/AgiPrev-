import { useEffect, useState } from "react";
import { Text } from "react-native";
import { router } from "expo-router";
import { useAuth } from "@/auth/AuthProvider";
import { Card, Badge, Button } from "@/components/ui";
import { ForecastChart } from "@/components/ForecastChart";
import { formatDecimal } from "@/features/banking/contracts";
import { useBankingVersion } from "@/features/banking/refresh";
import { errorMessage } from "@/services/errors";
import { ui } from "@/theme";
import { latestForecast, forecastSeries, retryForecastRefreshes } from "./api";
import type { LatestForecast, ForecastSeries } from "./contracts";
export function FinancialDashboard() {
  const account = useAuth().session?.accounts[0]?.id;
  const version = useBankingVersion();
  const [recovering, setRecovering] = useState(false);
  const [retry, setRetry] = useState(0);
  const [data, setData] = useState<{account: string; latest: LatestForecast; series: ForecastSeries | null} | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let active = true;
    if (!account) return;
    void (async () => {
      try {
        const latest = await latestForecast(account);
        const series = latest.forecast ? await forecastSeries(account, latest.forecast.id) : null;
        if (active) {setData({account, latest, series}); setError(null);}
      } catch (cause) {if (active) setError(errorMessage(cause));}
    })();
    return () => {active = false;};
  }, [account, version, retry]);
  const current = data?.account === account ? data : null;
  const run = current?.latest.forecast;
  const incomeCents = run?.points.reduce((sum, point) => sum + BigInt(point.income.replace(".", "")), 0n) ?? 0n;
  const income = `${incomeCents / 100n}.${(incomeCents % 100n).toString().padStart(2, "0")}`;
  const observed = current?.series?.points.filter(p => p.date <= current.series!.current_date && p.observed_balance !== null) ?? [];
  async function recover() {
    if (!account || recovering) return;
    setRecovering(true);
    try {
      const jobs = await retryForecastRefreshes(account);
      if (jobs.some(job => job.status === "failed")) setError("Não foi possível recalcular. A movimentação confirmada permanece preservada.");
      else {setError(null); setRetry(n => n + 1);}
    } catch (cause) {setError(errorMessage(cause));}
    finally {setRecovering(false);}
  }
  return <Card>
    <Text style={ui.heading}>Resumo da conta persistida</Text>
    {error && <Text accessibilityRole="alert">{error}{current ? " · Exibindo a última consulta; os dados podem estar desatualizados." : ""}</Text>}
    <Button secondary title="Atualizar previsão e saldo" onPress={() => setRetry(n => n + 1)} />
    {current && <Text style={ui.body}>Saldo atual confirmado: {formatDecimal(current.latest.current_balance)}</Text>}
    {current?.latest.stale && <><Badge tone="amber" text="Previsão obsoleta: gere novamente para atualizar a estimativa." /><Button secondary title={recovering ? "Recalculando…" : "Reprocessar atualização pendente"} disabled={recovering} onPress={() => void recover()} /></>}
    {current && !run && <Text style={ui.body}>Nenhuma previsão salva. Gere uma previsão abaixo.</Text>}
    {run && <>
      <Text style={ui.body}>Data-base {run.base_date} · horizonte {run.horizon} dias · versão {run.id}</Text>
      {run.experiment_id && <Text selectable style={ui.body}>Experimento {run.experiment_id} · {run.experiment_version ?? run.model_version}</Text>}
      <Badge tone={run.risk ? "amber" : "green"} text={run.risk ? `Risco de déficit em ${run.risk.date}: ${formatDecimal(run.risk.balance)}` : "Sem déficit previsto neste horizonte"} />
      <Text style={ui.body}>Saldo futuro: {formatDecimal(run.points.at(-1)!.balance)}. Previsões são estimativas, sem garantia.</Text>
      <Text style={ui.body}>Receitas previstas: {formatDecimal(income)}</Text>
      <ForecastChart dates={run.points.map(p => p.date)} series={[run.points.map(p => Number(p.balance) * 100), run.points.map(() => 0)]} labels={["Previsto", "Linha zero"]} />
      <Text style={ui.label}>Observado até {current?.series?.current_date}</Text>
      <ForecastChart dates={observed.map(p => p.date)} series={[observed.map(p => Number(p.observed_balance) * 100), observed.map(p => Number(p.predicted_balance) * 100), observed.map(() => 0)]} labels={["Observado", "Previsto anteriormente", "Linha zero"]} />
      {current?.series && <Text style={ui.body}>Gastos realizados: {formatDecimal(current.series.deviation.actual_expense)} · previstos: {formatDecimal(current.series.deviation.predicted_expense)} · diferença: {formatDecimal(current.series.deviation.amount)} · {current.series.deviation.percent === null ? "Percentual indisponível (base zero)" : `${current.series.deviation.percent}%`}. {current.series.deviation.alert_eligible ? "Há déficit previsto." : "Desvio isolado não gera alerta sem déficit previsto."}</Text>}
      <Button secondary title="Central de alertas" onPress={() => router.push("/alerts")} />
      <Button secondary title="Simular gasto pela API" onPress={() => router.push("/scenario")} />
    </>}
  </Card>;
}
