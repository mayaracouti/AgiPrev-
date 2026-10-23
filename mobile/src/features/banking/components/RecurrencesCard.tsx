import { useEffect, useState } from "react";
import { ActivityIndicator, Text } from "react-native";
import { useAuth } from "@/auth/AuthProvider";
import { request } from "@/services/http";
import { errorMessage } from "@/services/errors";
import { useBankingVersion } from "../refresh";
import { formatDecimal } from "../contracts";
import { Card, Button } from "@/components/ui";
import { ui } from "@/theme";
interface Recurrence {description: string; amount: string; direction: string; next_date: string; confidence: number}
export function RecurrencesCard() {
  const {session} = useAuth();
  const account = session?.accounts[0]?.id;
  const shared = useBankingVersion();
  const [retry, setRetry] = useState(0);
  const key = `${account}:${shared}:${retry}`;
  const [result, setResult] = useState<{key: string; rows: Recurrence[]; error: string | null} | null>(null);
  useEffect(() => {
    if (!account) return;
    const controller = new AbortController();
    void request<Recurrence[]>(`/accounts/${account}/recurrences`, {signal: controller.signal})
      .then(rows => {if (!controller.signal.aborted) setResult({key, rows, error: null});})
      .catch(cause => {if (!controller.signal.aborted) setResult({key, rows: [], error: errorMessage(cause)});});
    return () => controller.abort();
  }, [account, key]);
  const current = result?.key === key ? result : null;
  return <Card><Text style={ui.heading}>Recorrências do histórico persistido</Text>
    <Text style={ui.body}>Estimativas por heurística mensal. Regularidade observada, sem modelo treinado ou probabilidade calibrada.</Text>
    {!current ? <ActivityIndicator accessibilityLabel="Detectando recorrências" /> : current.error ? <><Text accessibilityRole="alert">{current.error}</Text><Button title="Tentar novamente" onPress={() => setRetry(value => value + 1)} /></> : <>
      {!current.rows.length && <Text style={ui.body}>São necessárias pelo menos três ocorrências regulares. Nenhum padrão mensal encontrado.</Text>}
      {current.rows.map(row => <Text key={row.direction + row.description} style={ui.body}>{row.description} · {formatDecimal(row.amount)} · prevista {row.next_date} · regularidade {Math.round(row.confidence * 100)}%</Text>)}
    </>}
  </Card>;
}
