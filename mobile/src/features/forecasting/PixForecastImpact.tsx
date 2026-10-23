import { useEffect, useState } from "react";
import { Text } from "react-native";
import { Card, Button } from "@/components/ui";
import { ForecastChart } from "@/components/ForecastChart";
import { formatDecimal } from "@/features/banking/contracts";
import { errorMessage } from "@/services/errors";
import { ui } from "@/theme";
import { forecastRun } from "./api";
import type { ForecastRun } from "./contracts";
export function PixForecastImpact({account, before, after}: {account: string; before: string; after: string}) {
  const [result, setResult] = useState<{key: string; previous: ForecastRun; current: ForecastRun} | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const key = `${account}:${before}:${after}`;
  useEffect(() => {
    let active = true;
    void Promise.all([forecastRun(account, before), forecastRun(account, after)]).then(([previous, current]) => {
      if (active) {setResult({key, previous, current}); setError(null);}
    }).catch(cause => {if (active) setError(errorMessage(cause));});
    return () => {active = false;};
  }, [account, before, after, key, retry]);
  const data = result?.key === key ? result : null;
  const points = data?.current.points.flatMap(point => {
    const previous = data.previous.points.find(p => p.date === point.date);
    return previous ? [{date: point.date, before: previous.balance, after: point.balance}] : [];
  }) ?? [];
  const last = points.at(-1);
  const delta = last ? BigInt(last.after.replace(".", "")) - BigInt(last.before.replace(".", "")) : 0n;
  const absolute = delta < 0n ? -delta : delta;
  const difference = `${delta < 0n ? "-" : ""}${absolute / 100n}.${(absolute % 100n).toString().padStart(2, "0")}`;
  return <Card>
    <Text style={ui.heading}>Impacto do Pix na previsão</Text>
    {error && <><Text accessibilityRole="alert">{error}. Pix confirmado; falha apenas ao consultar previsões.</Text><Button secondary title="Recarregar comparação" onPress={() => setRetry(n => n + 1)} /></>}
    {data && <Text style={ui.body}>Anterior {before} · nova {after}. Comparação apenas nas mesmas datas.</Text>}
    <ForecastChart dates={points.map(p => p.date)} series={[points.map(p => Number(p.before) * 100), points.map(p => Number(p.after) * 100)]} labels={["Antes do Pix", "Após o Pix"]} />
    {last && <Text style={ui.body}>Diferença em {last.date}: {formatDecimal(difference)}. Estimativas sem garantia.</Text>}
  </Card>;
}
