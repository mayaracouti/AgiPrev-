import { useEffect, useState } from "react";
import { Text } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { useAuth } from "@/auth/AuthProvider";
import { Button, Card, Badge } from "@/components/ui";
import { formatDecimal } from "@/features/banking/contracts";
import { errorMessage } from "@/services/errors";
import { enableLocalNotifications, notifyAlert } from "@/features/notifications";
import { ui } from "@/theme";
import { alerts, alertDetail, readAlert } from "./api";
import type { PreventiveAlert } from "./contracts";
export function AlertCenter() {
  const account = useAuth().session?.accounts[0]?.id;
  const {alertId} = useLocalSearchParams<{alertId?: string}>();
  const [result, setResult] = useState<{account: string; rows: PreventiveAlert[]} | null>(null);
  const [detail, setDetail] = useState<PreventiveAlert | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [permission, setPermission] = useState(false);
  const [notice, setNotice] = useState("");
  const [delivered, setDelivered] = useState<Set<string>>(new Set());
  const rows = result && result.account === account ? result.rows : [];
  async function open(id: string) {
    if (!account) return;
    try {setDetail(await alertDetail(account, id)); setError(null);} catch (cause) {setError(errorMessage(cause));}
  }
  useEffect(() => {
    let active = true;
    if (!account) return;
    void alerts(account).then(rows => {if (active) {setResult({account, rows}); setError(null);}}).catch(cause => {if (active) setError(errorMessage(cause));});
    return () => {active = false;};
  }, [account, retry]);
  useEffect(() => {
    let active = true;
    if (alertId && account) void alertDetail(account, alertId).then(row => {if (active) setDetail(row);}).catch(cause => {if (active) setError(errorMessage(cause));});
    return () => {active = false;};
  }, [alertId, account]);
  async function enable() {
    try {const granted = await enableLocalNotifications(); setPermission(granted); setNotice(granted ? "Permissão concedida. Use Notificar para testar a entrega local." : "Permissão negada. Seus alertas continuam disponíveis nesta central.");}
    catch (cause) {setError(errorMessage(cause));}
  }
  async function mark(id: string) {
    if (!account) return;
    try {const updated = await readAlert(account, id); setDetail(updated); setResult(previous => previous?.account === account ? {account, rows: previous.rows.map(row => row.id === id ? updated : row)} : previous);}
    catch (cause) {setError(errorMessage(cause));}
  }
  return <>
    <Card><Text style={ui.heading}>Alertas da conta persistida</Text>
      <Button secondary title="Atualizar alertas" onPress={() => setRetry(n => n + 1)} />
      <Button secondary title="Permitir notificações locais" onPress={() => void enable()} />
      <Text style={ui.body}>{notice || "Permissão solicitada apenas ao tocar no botão. Push remoto requer build compatível e não está habilitado."}</Text>
      {error && <Text accessibilityRole="alert">{error}</Text>}
      {result?.account === account && !rows.length && <Text style={ui.body}>Nenhum alerta persistido nesta conta.</Text>}
    </Card>
    {rows.map(row => <Card key={row.id}>
      <Badge tone={row.severity === "critical" ? "red" : "amber"} text={`${row.severity} · ${row.read_at ? "Lido" : "Não lido"}`} />
      <Text style={ui.heading}>{row.title}</Text>
      <Button secondary title={`Detalhes do alerta ${row.id}`} onPress={() => void open(row.id)} />
      {!row.read_at && <Button secondary title="Marcar como lido" onPress={() => void mark(row.id)} />}
      {permission && !delivered.has(row.id) && <Button secondary title="Notificar neste dispositivo" onPress={() => {
        if (!account) return;
        void notifyAlert(row.id, account, row.title, row.message).then(() => setDelivered(previous => new Set([...previous, row.id]))).catch(cause => setError(errorMessage(cause)));
      }} />}
    </Card>)}
    {detail && detail.account_id === account && <Card>
      <Text style={ui.heading}>{detail.title}</Text><Text style={ui.body}>{detail.message}</Text>
      <Text style={ui.body}>Data de risco {detail.risk_date} · déficit estimado {formatDecimal(detail.deficit)} · versão {detail.run_id}</Text>
      <Text style={ui.body}>{detail.recommendation}</Text>
      <Text style={ui.body}>Estimativa demonstrativa. Nenhum resultado é garantido.</Text>
    </Card>}
  </>;
}
