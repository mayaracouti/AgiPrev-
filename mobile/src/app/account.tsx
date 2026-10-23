import { errorMessage } from "@/services/errors";
import { useState } from "react";
import { router } from "expo-router";
import { Modal, Pressable, Switch, Text, TextInput, View } from "react-native";
import { useDemo } from "@/demo/DemoProvider";
import { dateLabel, profileOf, profiles } from "@/demo/model";
import { Screen, Card, Button, Chips, Badge } from "@/components/ui";
import { Icon } from "@/components/Icon";
import { ui, theme } from "@/theme";
export default function Account() {
  const { state, dispatch, signOut } = useDemo();
  const profile = profileOf(state.profileId);
  const [selected, setSelected] = useState(state.profileId);
  const [seed, setSeed] = useState(String(state.seed));
  const [message, setMessage] = useState("");
  const [confirmReset, setConfirmReset] = useState(false);
  function prepareReset() {
    if (!/^\d{1,10}$/.test(seed) || Number(seed) > 4294967295) {
      setMessage("Informe uma semente inteira de 0 a 4294967295.");
      return;
    }
    setConfirmReset(true);
  }
  return (
    <Screen
      title="Meu perfil"
      back
      subtitle="Preferências e controles do cenário visual; não alteram a conta do servidor."
    >
      <Card>
        <View style={ui.row}>
          <View
            style={{
              backgroundColor: "#DBE5FF",
              width: 58,
              height: 58,
              borderRadius: 29,
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Text style={[ui.heading, { color: theme.colors.primary }]}>
              {profile.initials}
            </Text>
          </View>
          <View style={{ flex: 1, gap: 5 }}>
            <Text style={ui.heading}>{profile.name}</Text>
            <Text style={ui.body}>{profile.description}</Text>
            <Badge text="Cenário fictício · controles locais" tone="green" />
          </View>
        </View>
      </Card>
      <Card>
        <View style={ui.row}>
          <Icon name="calendar" />
          <Text style={ui.heading}>Relógio simulado</Text>
        </View>
        <Text style={ui.amount}>{dateLabel(state.date)}</Text>
        <Text style={ui.body}>
          Ano {state.date.slice(0, 4)}. Avançar gera movimentações sintéticas
          para os dias decorridos e preserva as previsões anteriores. O relógio
          do computador não é alterado.
        </Text>
        <View style={ui.grid}>
          {[1, 7].map((days) => (
            <View key={days} style={{ flex: 1 }}>
              <Button
                secondary
                title={`Avançar ${days} dia${days > 1 ? "s" : ""}`}
                onPress={() => {
                  dispatch({ type: "advance", days });
                  setMessage(
                    `Relógio avançado em ${days} dia(s). Consulte Real × previsto no AgiPrevê.`,
                  );
                }}
              />
            </View>
          ))}
        </View>
        <Button
          secondary
          title="Ver comparação real × previsto"
          onPress={() => router.push("/(tabs)/agipreve")}
        />
      </Card>
      {message !== "" && (
        <Text accessibilityLiveRegion="polite" style={ui.body}>
          {message}
        </Text>
      )}
      <Card>
        <Text style={ui.heading}>Novo histórico sintético</Text>
        <Text style={ui.body}>
          Escolha um perfil e uma semente. A mesma combinação gera o mesmo
          histórico inicial. Reiniciar apaga as movimentações, versões e alertas
          desta sessão.
        </Text>
        <Chips
          values={profiles.map((p) => p.id)}
          value={selected}
          onChange={setSelected}
          label={(id) => profileOf(id).description}
        />
        <Text style={ui.label}>Semente dos dados</Text>
        <TextInput
          accessibilityLabel="Semente dos dados sintéticos"
          value={seed}
          onChangeText={setSeed}
          style={ui.input}
          keyboardType="number-pad"
          maxLength={10}
        />
        <Button secondary title="Gerar novo histórico" onPress={prepareReset} />
      </Card>
      <Card>
        <Text style={ui.heading}>Preferências de alertas</Text>
        <View style={ui.between}>
          <Text style={[ui.body, { flex: 1 }]}>Destacar alertas no início</Text>
          <Switch
            accessibilityLabel="Destacar alertas no início"
            value={state.notificationsEnabled}
            onValueChange={(enabled) =>
              dispatch({ type: "preferences", enabled })
            }
            trackColor={{ true: theme.colors.primary }}
          />
        </View>
        <Text style={ui.body}>
          Alertas permanecem no histórico. Notificações do sistema e push serão
          integradas posteriormente, mediante permissão do dispositivo.
        </Text>
        <Button
          secondary
          title="Abrir histórico de alertas"
          onPress={() => router.push("/alerts")}
        />
      </Card>
      <Card>
        <Text style={ui.heading}>Dados e segurança</Text>
        <Text style={ui.body}>
          A sessão é validada pelo servidor e só consulta a conta do cliente
          autenticado. Nunca informe CPF ou dados bancários reais. Os controles
          de cenário desta tela alteram apenas a demonstração visual.
        </Text>
      </Card>
      <Button
        secondary
        title="Sair do protótipo"
        onPress={() => {
          void signOut()
            .then(() => router.replace("/"))
            .catch((cause) => setMessage(errorMessage(cause)));
        }}
      />
      <Modal
        visible={confirmReset}
        transparent
        animationType="fade"
        onRequestClose={() => setConfirmReset(false)}
      >
        <View
          style={{
            flex: 1,
            backgroundColor: "#10204499",
            justifyContent: "center",
            padding: 24,
          }}
        >
          <Card>
            <Text style={ui.heading}>Reiniciar esta demonstração?</Text>
            <Text style={ui.body}>
              O histórico atual, os alertas e as versões locais serão
              substituídos. Essa alteração não pode ser desfeita.
            </Text>
            <Button
              title="Reiniciar com o novo perfil"
              onPress={() => {
                dispatch({
                  type: "reset",
                  profileId: selected,
                  seed: Number(seed),
                });
                setConfirmReset(false);
                setMessage(
                  "Histórico regenerado. A demonstração voltou a 23 de outubro de 2026.",
                );
              }}
            />
            <Pressable
              accessibilityRole="button"
              onPress={() => setConfirmReset(false)}
              style={{
                minHeight: 48,
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Text style={[ui.label, { color: theme.colors.primary }]}>
                Manter a demonstração atual
              </Text>
            </Pressable>
          </Card>
        </View>
      </Modal>
    </Screen>
  );
}
