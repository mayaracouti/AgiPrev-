import * as Notifications from "expo-notifications";
import { Platform } from "react-native";
export async function enableLocalNotifications(): Promise<boolean> {
  if (Platform.OS === "web") throw new Error("Notificações locais requerem Android ou iOS.");
  Notifications.setNotificationHandler({handleNotification: async () => ({shouldShowBanner: true, shouldShowList: true, shouldPlaySound: false, shouldSetBadge: false})});
  if (Platform.OS === "android") await Notifications.setNotificationChannelAsync("financial-alerts", {name: "Alertas demonstrativos", importance: Notifications.AndroidImportance.DEFAULT});
  const existing = await Notifications.getPermissionsAsync();
  const permissions = existing.granted ? existing : await Notifications.requestPermissionsAsync();
  return permissions.granted;
}
export async function notifyAlert(id: string, account: string, title: string, body: string) {
  return Notifications.scheduleNotificationAsync({identifier: `alert-${account}-${id}`, content: {title, body, data: {alertId: id, accountId: account}}, trigger: null});
}
export function observeNotificationOpening(open: (id: string, account: string) => void) {
  const handle = (response: Notifications.NotificationResponse) => {
    const data = response.notification.request.content.data;
    if (data && typeof data.alertId === "string" && typeof data.accountId === "string") open(data.alertId, data.accountId);
  };
  const listener = Notifications.addNotificationResponseReceivedListener(handle);
  void Notifications.getLastNotificationResponseAsync().then(response => {if (response) handle(response);}).catch(() => {});
  return () => listener.remove();
}
