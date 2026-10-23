import { useCallback, useEffect, useRef, useState } from "react";
import { Text, TextInput } from "react-native";
import { useAuth } from "@/auth/AuthProvider";
import { request } from "@/services/http";
import { ApiError, errorMessage } from "@/services/errors";
import { bankingUpdated } from "@/features/banking/refresh";
import { idempotencyKey, decimalInput } from "@/features/banking/inputs";
import { formatDecimal, type Scenario } from "@/features/banking/contracts";
import { Screen, Card, Button, Chips, Badge } from "@/components/ui";
import { ui } from "@/theme";
interface Recurrence {description: string; amount: string; next_date: string; confidence: number; occurrences: number}
export default function DevScenario() {
  const {session} = useAuth();
  const account = session?.accounts[0]?.id;
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [summary, setSummary] = useState<{transaction_count: number; first_date: string; last_date: string} | null>(null);
  const [recurrences, setRecurrences] = useState<Recurrence[]>([]);
  const [target, setTarget] = useState("");
  const [kind, setKind] = useState("extra_purchase");
  const [eventDate, setEventDate] = useState("");
  const [value, setValue] = useState("100,00");
  const [delay, setDelay] = useState("5");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const retry = useRef<{signature: string; key: string} | null>(null);
  const load = useCallback(async () => {
    return Promise.all([
      request<Scenario>(`/accounts/${account}/scenario`),
      request<typeof summary>(`/accounts/${account}/data-summary`),
      request<Recurrence[]>(`/accounts/${account}/recurrences`),
    ]);
  }, [account]);
  const apply = useCallback(([clock, data, detected]: Awaited<ReturnType<typeof load>>) => {
    setScenario(clock); setSummary(data); setRecurrences(detected);
  }, []);
  useEffect(() => {
    let active = true;
    if (account) void load().then(data => {if (active) apply(data);}).catch(cause => {if (active) setError(errorMessage(cause));});
    return () => {active = false;};
  }, [account, load, apply]);
  async function act(action: "advance" | "event") {
    if (inFlight.current || !account) return;
    inFlight.current = true; setBusy(true); setError("");
    try {
      let data: Record<string, string | number> = {target_date: target};
      if (action === "event") {
        const amount = decimalInput(value);
        if (!amount || !/^\d{1,2}$/.test(delay)) throw new ApiError(null, "INVALID_INPUT", "Informe valor e atraso válidos.");
        const signature = JSON.stringify({kind, eventDate, amount, delay});
        if (retry.current && retry.current.signature !== signature) throw new ApiError(null, "PENDING_RETRY", "Conclua o retry do evento anterior antes de alterar os campos.");
        retry.current ??= {signature, key: idempotencyKey()};
        data = {kind, scheduled_on: eventDate, amount, delay_days: Number(delay), idempotency_key: retry.current.key};
      }
      await request(`/accounts/${account}/scenario/${action === "advance" ? "advance" : "events"}`, {method: "POST", data});
      retry.current = null; bankingUpdated(); apply(await load());
    } catch(cause) {
      if (cause instanceof ApiError && cause.status !== null && cause.status < 500) retry.current = null;
      setError(errorMessage(cause));
    }
    finally {inFlight.current = false; setBusy(false);}
  }
  return <Screen back title="Cenário persistido · área dev" subtitle="Dados sintéticos e relógio virtual. Não altera o relógio do dispositivo.">
    <Badge text="Eventos sintéticos podem produzir saldo negativo" tone="amber" />
    {scenario && <Card><Text style={ui.heading}>Data: {scenario.current_date}</Text><Text style={ui.body}>Seed {scenario.seed} · {scenario.version}</Text><Text style={ui.body}>Saldo: {formatDecimal(scenario.balance)}</Text></Card>}
    {summary && <Card><Text style={ui.heading}>Resumo dos dados fictícios</Text><Text style={ui.body}>{summary.transaction_count} transações · {summary.first_date} a {summary.last_date}</Text></Card>}
    <Card><Text style={ui.heading}>Avançar relógio</Text><TextInput accessibilityLabel="Data destino" placeholder="AAAA-MM-DD" value={target} onChangeText={setTarget} maxLength={10} style={ui.input} /><Button title="Avançar data e processar eventos" disabled={busy} onPress={() => {void act("advance");}} /></Card>
    <Card><Text style={ui.heading}>Evento extraordinário</Text><Chips values={["extra_purchase", "extra_income", "salary_delay"]} value={kind} onChange={setKind} label={id => id === "salary_delay" ? "Atrasar salário" : id === "extra_income" ? "Receita eventual" : "Compra extraordinária"} />
      <Text style={ui.body}>Para atraso, informe a data do salário pendente.</Text><TextInput accessibilityLabel="Data do evento" placeholder="AAAA-MM-DD" value={eventDate} onChangeText={setEventDate} maxLength={10} style={ui.input} />
      {kind === "salary_delay" ? <TextInput accessibilityLabel="Dias de atraso" value={delay} onChangeText={setDelay} keyboardType="number-pad" style={ui.input} /> : <TextInput accessibilityLabel="Valor do evento" value={value} onChangeText={setValue} keyboardType="decimal-pad" style={ui.input} />}
      <Button title="Agendar evento fictício" disabled={busy} onPress={() => {void act("event");}} />
    </Card>
    <Card><Text style={ui.heading}>Próximos eventos agendados</Text><Text style={ui.body}>Saldo agendado considera apenas estes eventos conhecidos; não é previsão de um modelo.</Text>{scenario?.pending_events.slice(0, 12).map(event => <Text key={event.id} style={ui.body}>{event.date} · {event.description} · {formatDecimal(event.amount)} · saldo agendado {formatDecimal(event.scheduled_balance)}</Text>)}</Card>
    <Card><Text style={ui.heading}>Recorrências detectadas no histórico</Text><Text style={ui.body}>Heurística mensal; regularidade observada não é probabilidade calibrada. Valores são estimativas.</Text>{!recurrences.length && <Text style={ui.body}>Histórico insuficiente ou sem padrão mensal detectado.</Text>}{recurrences.map(row => <Text key={row.description + row.next_date} style={ui.body}>{row.description} · {formatDecimal(row.amount)} · prevista {row.next_date} · regularidade {Math.round(row.confidence * 100)}% ({row.occurrences} ocorrências)</Text>)}</Card>
    {error && <Text accessibilityRole="alert" style={ui.body}>{error}</Text>}
    <Button secondary title="Atualizar dados" disabled={busy} onPress={() => {void load().then(apply).catch(cause => setError(errorMessage(cause)));}} />
  </Screen>;
}
