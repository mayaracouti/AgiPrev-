import { useEffect, useState } from 'react';
import { ActivityIndicator, Text } from 'react-native';
import { request } from '@/services/http';
import { errorMessage } from '@/services/errors';
import { Card, Button, Badge } from './ui';
import { ui } from '@/theme';
export function ConnectivityCard() {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [message, setMessage] = useState('');
  async function check() {
    setStatus('loading');
    try {
      const response = await request<{ status: string }>('/health');
      if (response.status !== 'ok') throw new Error('Health response invalid');
      setStatus('ready');
    } catch (cause) { setMessage(errorMessage(cause)); setStatus('error'); }
  }
  useEffect(() => { void check(); }, []);
  return <Card><Text style={ui.label}>Conexão do protótipo</Text>{status === 'loading' ? <ActivityIndicator accessibilityLabel="Verificando API" /> : status === 'ready' ? <Badge text="API e banco disponíveis" tone="green" /> : <Text accessibilityRole="alert" style={ui.body}>{message}</Text>}<Button secondary title="Verificar conexão" disabled={status === 'loading'} onPress={() => { void check(); }} /></Card>;
}
