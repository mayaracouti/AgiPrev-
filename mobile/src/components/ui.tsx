import type { ReactNode } from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type ViewStyle,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router } from "expo-router";
import { Icon } from "./Icon";
import { theme, ui } from "@/theme";
import { DemoNotice } from "./DemoNotice";

export function Screen({
  children,
  title,
  subtitle,
  back = false,
}: {
  children: ReactNode;
  title: string;
  subtitle?: string;
  back?: boolean;
}) {
  return (
    <SafeAreaView edges={["top", "left", "right"]} style={styles.screen}>
      <ScrollView
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={styles.content}
      >
        {back && (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Voltar"
            onPress={() =>
              router.canGoBack() ? router.back() : router.replace("/(tabs)")
            }
            style={styles.back}
          >
            <Icon name="back" />
            <Text style={styles.link}>Voltar</Text>
          </Pressable>
        )}
        <View style={{ gap: 6 }}>
          <Text style={ui.kicker}>AGIPREVÊ · DEMONSTRAÇÃO</Text>
          <Text accessibilityRole="header" style={ui.title}>
            {title}
          </Text>
          {subtitle && <Text style={ui.body}>{subtitle}</Text>}
        </View>
        <DemoNotice />
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}
export function Card({
  children,
  style,
}: {
  children: ReactNode;
  style?: ViewStyle;
}) {
  return <View style={[ui.card, style]}>{children}</View>;
}
export function Button({
  title,
  onPress,
  secondary = false,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  secondary?: boolean;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondary,
        (pressed || disabled) && { opacity: 0.5 },
      ]}
    >
      <Text
        style={[
          styles.buttonText,
          secondary && { color: theme.colors.primary },
        ]}
      >
        {title}
      </Text>
    </Pressable>
  );
}
export function Section({
  title,
  action,
  onPress,
}: {
  title: string;
  action?: string;
  onPress?: () => void;
}) {
  return (
    <View style={ui.between}>
      <Text accessibilityRole="header" style={[ui.heading, { flex: 1 }]}>
        {title}
      </Text>
      {action && (
        <Pressable
          accessibilityRole="button"
          onPress={onPress}
          style={styles.linkTouch}
        >
          <Text style={styles.link}>{action}</Text>
        </Pressable>
      )}
    </View>
  );
}
export function Chips<T extends string | number>({
  values,
  value,
  onChange,
  label = String,
}: {
  values: readonly T[];
  value: T;
  onChange: (value: T) => void;
  label?: (value: T) => string;
}) {
  return (
    <View style={ui.grid}>
      {values.map((option) => (
        <Pressable
          key={option}
          accessibilityRole="button"
          accessibilityState={{ selected: value === option }}
          onPress={() => onChange(option)}
          style={[styles.chip, value === option && styles.chipActive]}
        >
          <Text
            style={{
              color: value === option ? "#FFFFFF" : theme.colors.muted,
              fontWeight: "700",
              fontSize: 12,
            }}
          >
            {label(option)}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}
export function Badge({
  text,
  tone = "blue",
}: {
  text: string;
  tone?: "blue" | "green" | "amber" | "red";
}) {
  const colors = {
    blue: ["#EEF3FF", "#1F4DD8"],
    green: ["#E8F7F0", "#16745A"],
    amber: ["#FFF2D6", "#8A5B10"],
    red: ["#FFF0F0", "#B63E47"],
  } as const;
  return (
    <View
      style={{
        backgroundColor: colors[tone][0],
        borderRadius: 8,
        paddingHorizontal: 10,
        paddingVertical: 7,
        alignSelf: "flex-start",
      }}
    >
      <Text style={{ color: colors[tone][1], fontWeight: "700", fontSize: 12 }}>
        {text}
      </Text>
    </View>
  );
}
export function Empty({ text }: { text: string }) {
  return (
    <Card>
      <Icon name="clock" color={theme.colors.muted} />
      <Text style={ui.body}>{text}</Text>
    </Card>
  );
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.colors.background },
  content: {
    padding: 22,
    paddingBottom: 48,
    gap: 20,
    maxWidth: 720,
    width: "100%",
    alignSelf: "center",
  },
  back: {
    minHeight: 44,
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    alignSelf: "flex-start",
  },
  button: {
    minHeight: 52,
    borderRadius: 14,
    backgroundColor: theme.colors.primary,
    padding: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "800",
    textAlign: "center",
  },
  secondary: { backgroundColor: theme.colors.paleBlue },
  link: { color: theme.colors.primary, fontSize: 13, fontWeight: "800" },
  linkTouch: { minHeight: 44, justifyContent: "center" },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  chipActive: {
    backgroundColor: theme.colors.primary,
    borderColor: theme.colors.primary,
  },
});
