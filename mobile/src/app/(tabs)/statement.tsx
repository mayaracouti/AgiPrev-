import { ActivityIndicator, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useLedger } from '@/features/banking/useLedger';
import { formatDecimal } from '@/features/banking/contracts';
import { Screen, Card, Button, Empty } from '@/components/ui';
import { dateLabel } from '@/demo/model';
import { ui } from '@/theme';
export default function Statement() {
  const { entries, loading, error, refresh, page, setPage } = useLedger();
  return <Screen title="Extrato" subtitle="Movimentações confirmadas no servidor, exclusivamente fictícias.">
    {loading ? <ActivityIndicator accessibilityLabel="Carregando extrato" /> : error ? <Card><Text accessibilityRole="alert" style={ui.body}>{error}</Text><Button title="Tentar novamente" onPress={refresh} /></Card> : entries.length ? <Card>{entries.map(entry => <View key={entry.id} style={{ gap: 5, paddingVertical: 12 }}><Text style={ui.label}>{entry.description}</Text><View style={ui.between}><Text style={ui.body}>{dateLabel(entry.occurred_on)}</Text><Text style={ui.label}>{entry.direction === 'credit' ? '+' : '−'} {formatDecimal(entry.amount)}</Text></View></View>)}</Card> : <Empty text="Nenhum lançamento confirmado nesta página." />}
    <View style={ui.grid}><View style={{ flex: 1 }}><Button secondary title="Anterior" disabled={page === 0 || loading} onPress={() => setPage(page - 1)} /></View><View style={{ flex: 1 }}><Button secondary title="Próxima" disabled={entries.length < 50 || loading} onPress={() => setPage(page + 1)} /></View></View>
    <Button secondary title="Atualizar extrato" disabled={loading} onPress={refresh} />
    <Button secondary title="Ver histórico do cenário visual" onPress={() => router.push('/scenario-history')} />
  </Screen>;
}
