import { Text } from "react-native";
import { useDemo } from "@/demo/DemoProvider";
import { dateLabel, money, realizedBalance } from "@/demo/model";
import { Screen, Card, Badge, Button, Empty } from "@/components/ui";
import { ui } from "@/theme";
export default function Alerts() {
  const { state, dispatch } = useDemo();
  return (
    <Screen
      back
      title="Seus alertas"
      subtitle="Contexto para agir com antecedência."
    >
      <Card>
        <Text style={ui.body}>
          Alertas internos do cenário ilustrativo. Não há envio de push nesta
          etapa. A preferência na Conta controla apenas o destaque visual dos
          alertas.
        </Text>
      </Card>
      {state.alerts.length === 0 && (
        <Empty text="Nenhum risco identificado pelas regras do cenário atual. Isso não garante ausência de risco financeiro." />
      )}
      {state.alerts.map((alert) => {
        const actual = realizedBalance(state, alert.targetDate);
        return (
          <Card key={alert.id}>
            <Badge
              text={alert.read ? "Lido" : "Novo alerta"}
              tone={alert.read ? "blue" : "amber"}
            />
            <Text style={ui.heading}>{alert.title}</Text>
            <Text style={ui.body}>{alert.message}</Text>
            <Text style={ui.body}>
              Emitido em {dateLabel(alert.date)} · versão {alert.snapshotId}
            </Text>
            <Text style={ui.body}>
              Saldo estimado no dia de risco: {money(alert.expectedBalance)}
            </Text>
            <Badge
              text={
                actual === null
                  ? "Resultado posterior: aguardando a data"
                  : actual < 0
                    ? "Realizado sintético: risco confirmado"
                    : "Realizado sintético: risco não confirmado"
              }
              tone={actual === null ? "blue" : actual < 0 ? "red" : "green"}
            />
            {actual !== null && (
              <Text style={ui.body}>
                Saldo realizado sintético: {money(actual)}
              </Text>
            )}
            {!alert.read && (
              <Button
                secondary
                title="Marcar como lido"
                onPress={() => dispatch({ type: "read", id: alert.id })}
              />
            )}
          </Card>
        );
      })}
    </Screen>
  );
}
