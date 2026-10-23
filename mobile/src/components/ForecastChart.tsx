import { useState } from "react";
import { Text, View } from "react-native";
import { LineChart } from "react-native-chart-kit";
import { theme, ui } from "@/theme";
import { dateLabel, money } from "@/demo/model";
export function ForecastChart({
  dates,
  series,
  labels,
}: {
  dates: string[];
  series: number[][];
  labels: string[];
}) {
  const [width, setWidth] = useState(0);
  const colors = ["#1F4DD8", "#21A27C", "#A6B4D0"];
  if (!dates.length)
    return (
      <Text style={ui.body}>
        Avance a data simulada para comparar valores realizados.
      </Text>
    );
  return (
    <View
      onLayout={(event) => setWidth(event.nativeEvent.layout.width)}
      style={{ gap: 12 }}
    >
      <Text style={[ui.body, { fontSize: 11 }]}>
        Valores em reais · {dateLabel(dates[0]!)} a{" "}
        {dateLabel(dates[dates.length - 1]!)}
      </Text>
      {dates.length === 1 && (
        <View style={{ gap: 8 }}>
          {labels.map((label, index) => (
            <Text key={label} style={ui.label}>
              {label}: {money(series[index]?.[0] ?? 0)}
            </Text>
          ))}
          <Text style={ui.body}>
            Um dia disponível. Avance mais um dia para visualizar as curvas.
          </Text>
        </View>
      )}
      {width > 0 && dates.length > 1 && (
        <View
          accessible
          accessibilityLabel={labels
            .map(
              (name, i) =>
                `${name}: último valor ${money(series[i]?.at(-1) ?? 0)}`,
            )
            .join(". ")}
        >
          <LineChart
            width={width}
            height={210}
            data={{
              labels: dates.map((d, i) =>
                i === 0 ||
                i === dates.length - 1 ||
                i === Math.floor(dates.length / 2)
                  ? dateLabel(d)
                  : "",
              ),
              datasets: series.map((data, i) => ({
                data: data.map((v) => v / 100),
                color: () => colors[i] ?? colors[0]!,
                strokeWidth: 2,
              })),
            }}
            chartConfig={{
              backgroundGradientFrom: "#FFFFFF",
              backgroundGradientTo: "#FFFFFF",
              color: () => "#1F4DD8",
              labelColor: () => "#66758E",
              decimalPlaces: 0,
              propsForBackgroundLines: {
                stroke: "#EDF0F6",
                strokeDasharray: "4 4",
              },
              propsForLabels: { fontSize: 10 },
            }}
            withDots={dates.length <= 7}
            withShadow={false}
            style={{ borderRadius: 12 }}
            formatYLabel={(value) => `${Math.round(Number(value))}`}
          />
        </View>
      )}
      <View style={ui.grid}>
        {labels.map((name, i) => (
          <View key={name} style={[ui.row, { gap: 6 }]}>
            <View
              style={{ width: 18, height: 3, backgroundColor: colors[i] }}
            />
            <Text style={{ color: theme.colors.muted, fontSize: 11 }}>
              {name}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}
