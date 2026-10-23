import { Text, View } from "react-native";
import { Icon } from "./Icon";
export function DemoNotice() {
  return (
    <View
      style={{
        backgroundColor: "#EEF3FF",
        borderRadius: 12,
        padding: 12,
        flexDirection: "row",
        gap: 9,
      }}
    >
      <Icon name="shield" size={17} />
      <Text style={{ flex: 1, fontSize: 11, lineHeight: 17, color: "#4663A4" }}>
        Protótipo demonstrativo não oficial, com dados fictícios. Sem integração
        com o Agibank.
      </Text>
    </View>
  );
}
