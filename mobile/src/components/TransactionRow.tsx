import { Text, View } from "react-native";
import { Icon } from "./Icon";
import { money, dateLabel } from "@/demo/model";
import type { Transaction } from "@/demo/types";
import { theme, ui } from "@/theme";
export function TransactionRow({
  item,
  visible = true,
}: {
  item: Transaction;
  visible?: boolean;
}) {
  const income = item.kind === "income";
  return (
    <View
      style={[
        ui.row,
        {
          minHeight: 76,
          borderBottomWidth: 1,
          borderBottomColor: theme.colors.border,
          paddingVertical: 10,
        },
      ]}
    >
      <View
        style={{
          width: 38,
          height: 38,
          borderRadius: 12,
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: income ? "#E8F7F0" : "#FFF0F0",
        }}
      >
        <Icon
          name={income ? "arrow-down" : "arrow-up"}
          color={income ? theme.colors.green : theme.colors.red}
          size={18}
        />
      </View>
      <View style={{ flex: 1, gap: 4 }}>
        <Text style={ui.label}>{item.description}</Text>
        <Text style={{ fontSize: 11, color: theme.colors.muted }}>
          {item.category} · {dateLabel(item.date)}
        </Text>
      </View>
      <Text
        style={{
          fontSize: 13,
          fontWeight: "800",
          color: income ? theme.colors.green : theme.colors.text,
        }}
      >
        {visible ? `${income ? "+" : "−"} ${money(item.cents)}` : "••••"}
      </Text>
    </View>
  );
}
