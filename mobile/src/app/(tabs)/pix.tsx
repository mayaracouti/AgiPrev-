import { Text } from "react-native";
import { router } from "expo-router";
import { Screen, Card, Button, Badge } from "@/components/ui";
import { ui } from "@/theme";
export default function Pix() {
  return <Screen title="Pix" subtitle="Envio simulado com comprovante no servidor.">
    <Card><Badge text="Protótipo · nenhuma transferência real" tone="amber" />
      <Text style={ui.body}>O Pix simulado debita sua conta fictícia uma única vez e aparece no extrato. Saídas acima do saldo são recusadas.</Text>
      <Button title="Enviar Pix simulado" onPress={() => router.push("/movement?kind=pix")} />
    </Card>
  </Screen>;
}
