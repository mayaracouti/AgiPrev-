import { useState } from "react";
import { ActivityIndicator, Text, TextInput, View } from "react-native";
import { useAuth } from "@/auth/AuthProvider";
import { useLedger, type HistoryFilters } from "@/features/banking/useLedger";
import { useCategories } from "@/features/banking/useCategories";
import { bankingUpdated } from "@/features/banking/refresh";
import { formatDecimal } from "@/features/banking/contracts";
import { request } from "@/services/http";
import { errorMessage } from "@/services/errors";
import { Screen, Card, Button, Chips, Empty } from "@/components/ui";
import { ui } from "@/theme";
export default function Statement() {
  const {session} = useAuth();
  const account = session?.accounts[0]?.id;
  const [filters, setFilters] = useState<HistoryFilters>({});
  const [draft, setDraft] = useState<HistoryFilters>({});
  const ledger = useLedger(filters);
  const {categories, error: categoryError} = useCategories();
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function categorize(id: string, category_id: string) {
    setBusy(true); setError("");
    try { await request(`/accounts/${account}/transactions/${id}/category`, {method: "PATCH", data: {category_id}}); setEditing(null); bankingUpdated(); }
    catch(cause) {setError(errorMessage(cause));}
    finally {setBusy(false);}
  }
  return <Screen title="Extrato" subtitle="Movimentações confirmadas no servidor · dados fictícios.">
    <Card>
      <Text style={ui.label}>Buscar descrição</Text><TextInput accessibilityLabel="Buscar descrição" style={ui.input} value={draft.search ?? ""} onChangeText={search => setDraft({...draft, search})} />
      <Text style={ui.label}>Período (AAAA-MM-DD)</Text>
      <TextInput accessibilityLabel="Data inicial" placeholder="Data inicial: AAAA-MM-DD" style={ui.input} value={draft.date_from ?? ""} onChangeText={date_from => setDraft({...draft, date_from})} maxLength={10} />
      <TextInput accessibilityLabel="Data final" placeholder="Data final: AAAA-MM-DD" style={ui.input} value={draft.date_to ?? ""} onChangeText={date_to => setDraft({...draft, date_to})} maxLength={10} />
      <Chips values={["", "credit", "debit"]} value={draft.direction ?? ""} onChange={direction => setDraft({...draft, direction})} label={id => id === "credit" ? "Entradas" : id === "debit" ? "Saídas" : "Todas"} />
      <Chips values={["", ...categories.map(c => c.id)]} value={draft.category_id ?? ""} onChange={category_id => setDraft({...draft, category_id})} label={id => categories.find(c => c.id === id)?.name ?? "Todas as categorias"} />
      <Button title="Aplicar filtros" onPress={() => setFilters({...draft})} />
      <Button secondary title="Limpar filtros" onPress={() => {setDraft({}); setFilters({});}} />
    </Card>
    {ledger.loading ? <ActivityIndicator accessibilityLabel="Carregando extrato" /> : ledger.error ? <Card><Text accessibilityRole="alert" style={ui.body}>{ledger.error}</Text><Button title="Tentar novamente" onPress={ledger.refresh} /></Card> : <>
      <Text style={ui.body}>{ledger.total} movimentações · página {ledger.page + 1}</Text>
      {!ledger.entries.length && <Empty text="Nenhuma movimentação neste período." />}
      {ledger.entries.map(entry => <Card key={entry.id}>
        <Text style={ui.label}>{entry.description}</Text><Text style={ui.body}>{entry.occurred_on} · {categories.find(c => c.id === entry.category_id)?.name ?? entry.category_id}</Text>
        <Text style={ui.heading}>{entry.direction === "credit" ? "+" : "−"} {formatDecimal(entry.amount)}</Text>
        {entry.recipient && <Text style={ui.body}>Favorecido fictício: {entry.recipient}</Text>}
        <Button secondary title="Editar categoria" onPress={() => setEditing(editing === entry.id ? null : entry.id)} disabled={busy} />
        {editing === entry.id && !busy && <Chips values={categories.map(c => c.id)} value={entry.category_id} label={id => categories.find(c => c.id === id)?.name ?? id} onChange={id => {void categorize(entry.id, id);}} />}
      </Card>)}
      <View style={ui.grid}><Button secondary title="Anterior" disabled={ledger.page === 0} onPress={ledger.previous} /><Button secondary title="Próxima" disabled={!ledger.hasNext} onPress={ledger.next} /></View>
    </>}
    {(error || categoryError) && <Text accessibilityRole="alert" style={ui.body}>{error || categoryError}</Text>}
    <Button secondary title="Atualizar extrato" onPress={ledger.refresh} />
  </Screen>;
}
