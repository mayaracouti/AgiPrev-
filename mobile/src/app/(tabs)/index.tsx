import { useAuth } from "@/auth/AuthProvider";
import { useBalance } from "@/features/banking/useBalance";
import { BalanceCard } from "@/features/banking/components/BalanceCard";
import { formatDecimal } from "@/features/banking/contracts";
import { ConnectivityCard } from "@/components/ConnectivityCard";
import { useState } from "react";
import { router } from "expo-router";
import { Pressable, ScrollView, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { DemoNotice } from "@/components/DemoNotice";
import { Icon, type IconName } from "@/components/Icon";
import { Badge, Button, Card, Section } from "@/components/ui";
import { TransactionRow } from "@/components/TransactionRow";
import { useDemo } from "@/demo/DemoProvider";
import { currentSnapshot, dateLabel, money, profileOf } from "@/demo/model";
import { theme, ui } from "@/theme";
export default function Home() {
  const { state, balance } = useDemo();
  const { session } = useAuth();
  const bankBalance = useBalance();
  const [visible, setVisible] = useState(true);
  const insets = useSafeAreaInsets();
  const profile = profileOf(state.profileId);
  const snapshot = currentSnapshot(state);
  const risk = snapshot.points.find((p) => p.balance < 0);
  const unread = state.notificationsEnabled
    ? state.alerts.filter((a) => !a.read).length
    : 0;
  const actions: { label: string; icon: IconName; kind: string }[] = [
    { label: "Pix", icon: "pix", kind: "pix" },
    { label: "Receber", icon: "arrow-down", kind: "income" },
    { label: "Pagar", icon: "arrow-up", kind: "expense" },
    { label: "Extrato", icon: "clock", kind: "history" },
  ];
  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <ScrollView contentContainerStyle={{ paddingBottom: 32 }}>
        <LinearGradient
          colors={["#173BB8", "#2160E8"]}
          style={{
            paddingTop: insets.top + 18,
            paddingHorizontal: 22,
            paddingBottom: 28,
            borderBottomLeftRadius: 28,
            borderBottomRightRadius: 28,
          }}
        >
          <View
            style={[
              ui.between,
              { maxWidth: 676, width: "100%", alignSelf: "center" },
            ]}
          >
            <View style={ui.row}>
              <View
                style={{
                  backgroundColor: "#DBE5FF",
                  width: 44,
                  height: 44,
                  borderRadius: 22,
                  justifyContent: "center",
                  alignItems: "center",
                }}
              >
                <Text style={{ color: "#2449B5", fontWeight: "800" }}>
                  {profile.initials}
                </Text>
              </View>
              <View>
                <Text
                  style={{ color: "#FFFFFF", fontWeight: "700", fontSize: 16 }}
                >
                  Olá, {session?.customer.name.split(" ")[0]}!
                </Text>
                <Text style={{ color: "#D5E2FF", fontSize: 12, marginTop: 4 }}>
                  Seu dinheiro em movimento
                </Text>
              </View>
            </View>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Alertas, ${unread} não lidos`}
              onPress={() => router.push("/alerts")}
              style={{
                padding: 12,
                backgroundColor: "#355DD0",
                borderRadius: 24,
              }}
            >
              <Icon name="bell" color="#FFFFFF" />
              {unread > 0 && (
                <View
                  style={{
                    position: "absolute",
                    top: 6,
                    right: 8,
                    width: 8,
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: "#FFCF5C",
                  }}
                />
              )}
            </Pressable>
          </View>
          <View
            style={{
              marginTop: 30,
              maxWidth: 676,
              width: "100%",
              alignSelf: "center",
              gap: 8,
            }}
          >
            <Text style={{ color: "#D5E2FF", fontSize: 13 }}>
              Saldo disponível
            </Text>
            <View style={ui.between}>
              <Text
                style={{
                  color: "#FFFFFF",
                  fontSize: 34,
                  fontWeight: "800",
                  flexShrink: 1,
                }}
              >
                {visible
                  ? bankBalance.data
                    ? formatDecimal(bankBalance.data.balance)
                    : bankBalance.loading
                      ? "Consultando…"
                      : "Indisponível"
                  : "R$ ••••••"}
              </Text>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={
                  visible ? "Ocultar valores" : "Mostrar valores"
                }
                onPress={() => setVisible(!visible)}
                style={{ padding: 12 }}
              >
                <Icon name="eye" color="#D5E2FF" />
              </Pressable>
            </View>
            <Text style={{ color: "#D5E2FF", fontSize: 12 }}>
              Conta fictícia · {dateLabel(state.date)} de{" "}
              {state.date.slice(0, 4)}
            </Text>
            <View style={[ui.between, { marginTop: 16 }]}>
              {actions.map((action) => (
                <Pressable
                  key={action.kind}
                  accessibilityRole="button"
                  onPress={() =>
                    action.kind === "history"
                      ? router.push("/transactions")
                      : router.push({
                          pathname: "/movement",
                          params: { kind: action.kind },
                        })
                  }
                  style={{
                    alignItems: "center",
                    gap: 8,
                    minWidth: 54,
                    paddingVertical: 4,
                  }}
                >
                  <View
                    style={{
                      width: 48,
                      height: 48,
                      borderRadius: 24,
                      backgroundColor: "#FFFFFF",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Icon name={action.icon} />
                  </View>
                  <Text
                    style={{
                      color: "#FFFFFF",
                      fontWeight: "700",
                      fontSize: 12,
                    }}
                  >
                    {action.label}
                  </Text>
                </Pressable>
              ))}
            </View>
          </View>
        </LinearGradient>
        <View
          style={{
            padding: 22,
            gap: 18,
            maxWidth: 720,
            width: "100%",
            alignSelf: "center",
          }}
        >
          <DemoNotice />
          <BalanceCard
            data={bankBalance.data}
            loading={bankBalance.loading}
            error={bankBalance.error}
            onRetry={() => {
              void bankBalance.refresh();
            }}
            visible={visible}
          />
          <Button
            secondary
            title="Conta e preferências"
            onPress={() => router.push("/account")}
          />
          <ConnectivityCard />
          <Card>
            <Badge text="Cenário visual independente" tone="amber" />
            <Text style={ui.body}>
              Saldo do cenário: {visible ? money(balance) : "••••"}. Pix,
              receitas e despesas deste cenário são independentes da conta. Os atalhos acima gravam no servidor.
              Não substituem o saldo confirmado no servidor.
            </Text>
          </Card>
          <Section
            title="AgiPrevê"
            action="Ver análise"
            onPress={() => router.push("/(tabs)/agipreve")}
          />
          <Card
            style={{
              backgroundColor: risk ? "#FFF8E8" : "#EAF1FF",
              borderWidth: 0,
            }}
          >
            <View style={ui.row}>
              <Icon
                name="sparkles"
                color={risk ? theme.colors.amber : theme.colors.primary}
              />
              <Text style={[ui.heading, { flex: 1, fontSize: 16 }]}>
                {risk
                  ? "Vamos olhar os próximos dias?"
                  : "Seu planejamento começa aqui"}
              </Text>
            </View>
            <Text style={ui.body}>
              {risk
                ? `O cenário ilustrativo indica saldo negativo em ${dateLabel(risk.date)}. Veja quais despesas influenciam essa estimativa.`
                : "O cenário ilustrativo mantém seu saldo positivo no horizonte de 30 dias. Continue acompanhando as movimentações."}
            </Text>
            <Badge
              text="Cenário demonstrativo · não é garantia"
              tone={risk ? "amber" : "blue"}
            />
          </Card>
          <Section
            title="Movimentações do cenário"
            action="Ver cenário"
            onPress={() => router.push("/scenario-history")}
          />
          <Card>
            {[...state.transactions]
              .reverse()
              .slice(0, 4)
              .map((tx) => (
                <TransactionRow key={tx.id} item={tx} visible={visible} />
              ))}
          </Card>
          <LinearGradient
            colors={["#173BB8", "#2458DA"]}
            style={{ borderRadius: 20, padding: 22, gap: 12 }}
          >
            <Text
              style={{
                color: "#BDD1FF",
                fontSize: 11,
                fontWeight: "800",
                letterSpacing: 1,
              }}
            >
              VEJA O IMPACTO ANTES DE DECIDIR
            </Text>
            <Text style={[ui.heading, { color: "#FFFFFF", fontSize: 22 }]}>
              E se eu fizer esse gasto?
            </Text>
            <Text style={{ color: "#D9E5FF", lineHeight: 21 }}>
              Explore um cenário sem movimentar o saldo da sua conta.
            </Text>
            <Button
              secondary
              title="Simular um gasto"
              onPress={() => router.push("/scenario")}
            />
          </LinearGradient>
        </View>
      </ScrollView>
    </View>
  );
}
