import { AuthProvider } from "@/auth/AuthProvider";
import { Stack } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "react-native";
import { DemoProvider, useDemo } from "@/demo/DemoProvider";
function Navigation() {
  const { signedIn } = useDemo();
  return (
    <>
      <StatusBar barStyle="dark-content" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Protected guard={signedIn}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="transactions" />
          <Stack.Screen name="account" />
          <Stack.Screen name="dev-scenario" />
          <Stack.Screen name="local-movement" options={{ presentation: "modal" }} />
          <Stack.Screen name="scenario-history" />
          <Stack.Screen name="movement" options={{ presentation: "modal" }} />
          <Stack.Screen name="alerts" />
          <Stack.Screen name="scenario" />
          <Stack.Screen name="versions" />
        </Stack.Protected>
      </Stack>
    </>
  );
}
export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <DemoProvider>
          <Navigation />
        </DemoProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
