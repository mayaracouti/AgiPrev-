import { Text } from "react-native";
import { router } from "expo-router";
import { Screen, Card, Button, Badge } from "@/components/ui";
import { ui } from "@/theme";
export default function Pix() {
  return (
    <Screen
      title="Pix"
      subtitle="Experimente o fluxo sem transferir dinheiro real."
    >
      <Card>
        <Badge
          text="Simulação visual · sem lançamento no servidor"
          tone="amber"
        />
        <Text style={ui.body}>
          O fluxo já permite explorar como um Pix afeta um cenário local. A
          gravação de movimentações na conta será integrada na próxima etapa do
          banco simulado.
        </Text>
        <Text style={ui.body}>
          O saldo confirmado e o extrato do servidor não são alterados por esta
          simulação.
        </Text>
        <Button
          title="Abrir simulação de Pix"
          onPress={() => router.push("/movement?kind=pix")}
        />
      </Card>
    </Screen>
  );
}
