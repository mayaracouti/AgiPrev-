import { useEffect, useState } from 'react';
import { Redirect } from 'expo-router';
import { ActivityIndicator, Text, TextInput, View, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '@/auth/AuthProvider';
import { Screen, Button, Card, Badge, Empty } from '@/components/ui';
import { ConnectivityCard } from '@/components/ConnectivityCard';
import { Icon } from '@/components/Icon';
import { ui, theme } from '@/theme';
export default function Welcome() {
  const { session, customers, loading, error, loadCustomers, login } = useAuth();
  const [selected, setSelected] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  useEffect(() => { void loadCustomers(); }, [loadCustomers]);
  if (session) return <Redirect href="/(tabs)" />;
  return <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}><Screen title="Seu dinheiro, um passo à frente." subtitle="Acesse uma conta fictícia do protótipo AgiPrevê.">
    <LinearGradient colors={['#173BB8', '#2160E8']} style={{ padding: 26, borderRadius: 24, gap: 16 }}><Icon name="sparkles" color="#C5D9FF" size={36} /><Text style={[ui.title, { color: '#FFFFFF' }]}>Mais clareza hoje. Mais tranquilidade amanhã.</Text><Text style={{ color: '#D9E5FF', lineHeight: 21 }}>Dados exclusivamente fictícios. Sem acesso a serviços bancários reais.</Text></LinearGradient>
    <Text style={ui.heading}>Escolha um cliente fictício</Text>
    {loading && <ActivityIndicator accessibilityLabel="Carregando perfis ou sessão" />}
    {!loading && !customers.length && <Empty text="Nenhum perfil disponível. Verifique a conexão e se o seed foi executado no servidor." />}
    {customers.map(customer => <Pressable disabled={loading} key={customer.id} accessibilityRole="button" accessibilityState={{ selected: selected === customer.email }} onPress={() => setSelected(customer.email)}><Card style={{ borderColor: selected === customer.email ? theme.colors.primary : theme.colors.border }}><View style={ui.between}><View style={{ flex: 1, gap: 5 }}><Text style={ui.label}>{customer.name}</Text><Text style={ui.body}>{customer.email}</Text></View>{selected === customer.email && <Icon name="check" />}</View></Card></Pressable>)}
    <Text style={ui.label}>Senha de desenvolvimento</Text><TextInput accessibilityLabel="Senha demonstrativa" value={password} onChangeText={setPassword} style={ui.input} secureTextEntry autoCapitalize="none" autoCorrect={false} maxLength={128} placeholder="Senha fictícia configurada no ambiente" />
    <Badge text="Não use uma senha pessoal ou bancária" />
    {error && <Text accessibilityRole="alert" style={{ color: theme.colors.red }}>{error}</Text>}
    <Button title={loading ? 'Conectando…' : 'Entrar no protótipo'} disabled={loading || !selected || !password} onPress={() => { if (selected) void login(selected, password).then(() => setPassword('')).catch(() => undefined); }} />
    <Button secondary title="Atualizar lista de clientes" disabled={loading} onPress={() => { void loadCustomers(); }} />
    <ConnectivityCard />
  </Screen></KeyboardAvoidingView>;
}
