import { ActivityIndicator, Text } from "react-native";
import { Button, Card, Empty } from "@/components/ui";
import { ui } from "@/theme";
import { formatDecimal, type BalanceResponse } from "../contracts";
export function BalanceCard({
  data,
  loading,
  error,
  onRetry,
  visible = true,
}: {
  data: BalanceResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  visible?: boolean;
}) {
  return (
    <Card>
      <Text style={ui.label}>Saldo confirmado no servidor</Text>
      {loading ? (
        <>
          <ActivityIndicator accessibilityLabel="Carregando saldo" />
          <Text style={ui.body}>Consultando sua conta fictícia…</Text>
        </>
      ) : error ? (
        <>
          <Text accessibilityRole="alert" style={ui.body}>
            {error}
          </Text>
          <Button secondary title="Tentar novamente" onPress={onRetry} />
        </>
      ) : data ? (
        <Text testID="account-balance" style={ui.amount}>
          {visible ? formatDecimal(data.balance) : "R$ ••••••"}
        </Text>
      ) : (
        <Empty text="Nenhuma conta disponível." />
      )}
      <Text style={ui.body}>
        Créditos menos débitos confirmados no ledger. Nenhum valor local
        substitui esta consulta.
      </Text>
    </Card>
  );
}
