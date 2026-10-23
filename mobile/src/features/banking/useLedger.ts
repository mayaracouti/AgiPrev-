import { useEffect, useState, useCallback } from 'react';
import { useAuth } from '@/auth/AuthProvider';
import { request } from '@/services/http';
import { ApiError, errorMessage } from '@/services/errors';
import type { LedgerEntry } from './contracts';
export function useLedger() {
  const { session } = useAuth();
  const account = session?.accounts[0]?.id;
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const refresh = useCallback(() => setVersion(value => value + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    setEntries([]); setError(null); setLoading(true);
    if (!account) { setLoading(false); return; }
    void request<LedgerEntry[]>(`/accounts/${account}/ledger?limit=50&offset=${page * 50}`, { signal: controller.signal }).then(data => {
      if (!Array.isArray(data) || data.some(item => !item.id || !['credit', 'debit'].includes(item.direction) || !/^\d+\.\d{2}$/.test(item.amount))) throw new ApiError(null, 'INVALID_RESPONSE', 'O servidor retornou um extrato inválido.');
      if (!controller.signal.aborted) setEntries(data);
    }).catch(cause => { if (!controller.signal.aborted) setError(errorMessage(cause)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [account, page, version]);
  return { entries, loading, error, refresh, page, setPage };
}
