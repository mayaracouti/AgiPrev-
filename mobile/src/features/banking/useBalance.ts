import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '@/auth/AuthProvider';
import { request } from '@/services/http';
import { ApiError, errorMessage } from '@/services/errors';
import { isBalanceResponse, type BalanceResponse } from './contracts';
export function useBalance() {
  const { session } = useAuth();
  const accountId = session?.accounts[0]?.id;
  const [data, setData] = useState<BalanceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const active = useRef<AbortController | null>(null);
  const refresh = useCallback(async () => {
    active.current?.abort();
    const controller = new AbortController(); active.current = controller;
    setData(null); setError(null);
    if (!accountId) { setLoading(false); return; }
    setLoading(true);
    try {
      const result: unknown = await request(`/accounts/${accountId}/balance`, { signal: controller.signal });
      if (!isBalanceResponse(result, accountId)) throw new ApiError(null, 'INVALID_RESPONSE', 'Não foi possível validar o saldo recebido.');
      if (!controller.signal.aborted) setData(result);
    } catch (cause) { if (!controller.signal.aborted) setError(errorMessage(cause)); }
    finally { if (!controller.signal.aborted) setLoading(false); }
  }, [accountId]);
  useEffect(() => { void refresh(); return () => active.current?.abort(); }, [refresh]);
  return { data, loading, error, refresh };
}
