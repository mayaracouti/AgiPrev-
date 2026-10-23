import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/auth/AuthProvider";
import { request } from "@/services/http";
import { ApiError, errorMessage } from "@/services/errors";
import { isBalanceResponse, type BalanceResponse } from "./contracts";
import { useBankingVersion } from "./refresh";
export function useBalance() {
  const sharedVersion = useBankingVersion();
  const { session } = useAuth();
  const accountId = session?.accounts[0]?.id;
  const [localVersion, setVersion] = useState(0);
  const version = `${sharedVersion}:${localVersion}`;
  const [result, setResult] = useState<{
    account: string;
    version: string;
    data: BalanceResponse | null;
    error: string | null;
  } | null>(null);
  const refresh = useCallback(() => setVersion((value) => value + 1), []);
  useEffect(() => {
    if (!accountId) return;
    const controller = new AbortController();
    void request<unknown>(`/accounts/${accountId}/balance`, {
      signal: controller.signal,
    })
      .then((data) => {
        if (!isBalanceResponse(data, accountId))
          throw new ApiError(
            null,
            "INVALID_RESPONSE",
            "Não foi possível validar o saldo recebido.",
          );
        if (!controller.signal.aborted)
          setResult({ account: accountId, version, data, error: null });
      })
      .catch((cause) => {
        if (!controller.signal.aborted)
          setResult({
            account: accountId,
            version,
            data: null,
            error: errorMessage(cause),
          });
      });
    return () => controller.abort();
  }, [accountId, version]);
  const current =
    result?.account === accountId && result?.version === version
      ? result
      : null;
  return {
    data: current?.data ?? null,
    loading: Boolean(accountId && !current),
    error: current?.error ?? null,
    refresh,
  };
}
