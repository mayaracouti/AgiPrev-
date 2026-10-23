import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@/auth/AuthProvider";
import { request } from "@/services/http";
import { errorMessage } from "@/services/errors";
import { useBankingVersion } from "./refresh";
import type { TransactionPage } from "./contracts";
export interface HistoryFilters { date_from?: string; date_to?: string; category_id?: string; direction?: string; search?: string }
export function useLedger(filters: HistoryFilters = {}) {
  const { session } = useAuth();
  const account = session?.accounts[0]?.id;
  const shared = useBankingVersion();
  const [version, setVersion] = useState(0);
  const [navigation, setNavigation] = useState<{scope: string; cursors: (string | null)[]}>({scope: "", cursors: [null]});
  const query = new URLSearchParams(Object.entries(filters).filter(([,value]) => Boolean(value)) as [string,string][]).toString();
  const scope = `${account}:${query}:${shared}:${version}`;
  const cursors = navigation.scope === scope ? navigation.cursors : [null];
  const cursor = cursors[cursors.length - 1];
  const key = `${scope}:${cursor ?? ""}`;
  const [result, setResult] = useState<{ key: string; data: TransactionPage | null; error: string | null } | null>(null);
  const refresh = useCallback(() => setVersion((value) => value + 1), []);
  useEffect(() => {
    if (!account) return;
    const controller = new AbortController();
    void request<TransactionPage>(`/accounts/${account}/transactions?limit=25&${query}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`, { signal: controller.signal })
      .then((data) => {
        if (!Array.isArray(data.items)) throw new Error("Extrato inválido.");
        if (!controller.signal.aborted) setResult({ key, data, error: null });
      }).catch((cause) => {
        if (!controller.signal.aborted) setResult({ key, data: null, error: errorMessage(cause) });
      });
    return () => controller.abort();
  }, [account, query, cursor, key]);
  const current = result?.key === key ? result : null;
  const nextCursor = current?.data?.next_cursor;
  return {
    entries: current?.data?.items ?? [], total: current?.data?.total ?? 0,
    loading: Boolean(account && !current), error: current?.error ?? null, refresh,
    page: cursors.length - 1, hasNext: Boolean(nextCursor),
    next: () => { if (nextCursor) setNavigation({scope, cursors: [...cursors, nextCursor]}); },
    previous: () => setNavigation({scope, cursors: cursors.slice(0, -1)}),
  };
}
