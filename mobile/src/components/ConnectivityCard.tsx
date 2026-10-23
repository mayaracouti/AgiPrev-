import { useEffect, useState } from "react";
import { ActivityIndicator, Text } from "react-native";
import { request } from "@/services/http";
import { errorMessage } from "@/services/errors";
import { Card, Button, Badge } from "./ui";
import { ui } from "@/theme";
export function ConnectivityCard() {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<{
    version: number;
    error: string | null;
  } | null>(null);
  const loading = result?.version !== version;
  useEffect(() => {
    const controller = new AbortController();
    void request<{ status: string }>("/health", { signal: controller.signal })
      .then((response) => {
        if (response.status !== "ok")
          throw new Error("Invalid health response");
        if (!controller.signal.aborted) setResult({ version, error: null });
      })
      .catch((cause) => {
        if (!controller.signal.aborted)
          setResult({ version, error: errorMessage(cause) });
      });
    return () => controller.abort();
  }, [version]);
  return (
    <Card>
      <Text style={ui.label}>Conexão do protótipo</Text>
      {loading ? (
        <ActivityIndicator accessibilityLabel="Verificando API" />
      ) : result?.error ? (
        <Text accessibilityRole="alert" style={ui.body}>
          {result.error}
        </Text>
      ) : (
        <Badge text="API e banco disponíveis" tone="green" />
      )}
      <Button
        secondary
        title="Verificar conexão"
        disabled={loading}
        onPress={() => setVersion((value) => value + 1)}
      />
    </Card>
  );
}
