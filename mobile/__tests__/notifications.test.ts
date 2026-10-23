import * as Notifications from "expo-notifications";
import { enableLocalNotifications, notifyAlert, observeNotificationOpening } from "@/features/notifications";
jest.mock("expo-notifications", () => ({
  AndroidImportance: {DEFAULT: 3}, setNotificationHandler: jest.fn(), setNotificationChannelAsync: jest.fn(), getPermissionsAsync: jest.fn(), requestPermissionsAsync: jest.fn(),
  scheduleNotificationAsync: jest.fn(), addNotificationResponseReceivedListener: jest.fn(), getLastNotificationResponseAsync: jest.fn(),
}));
beforeEach(() => {
  jest.resetAllMocks();
  jest.mocked(Notifications.getLastNotificationResponseAsync).mockResolvedValue(null);
  jest.mocked(Notifications.addNotificationResponseReceivedListener).mockReturnValue({remove: jest.fn()});
});
test("permission denied does not schedule a notification; scheduling contains account scoped navigation data", async () => {
  jest.mocked(Notifications.getPermissionsAsync).mockResolvedValue({granted: false} as never);
  jest.mocked(Notifications.requestPermissionsAsync).mockResolvedValue({granted: false} as never);
  expect(await enableLocalNotifications()).toBe(false);
  expect(Notifications.scheduleNotificationAsync).not.toHaveBeenCalled();
  await notifyAlert("alert", "account", "Risco", "Estimativa");
  expect(Notifications.scheduleNotificationAsync).toHaveBeenCalledWith({identifier: "alert-account-alert", content: {title: "Risco", body: "Estimativa", data: {alertId: "alert", accountId: "account"}}, trigger: null});
});
test("notification opening validates navigation metadata and removes listener", () => {
  const open = jest.fn();
  const stop = observeNotificationOpening(open);
  const listener = jest.mocked(Notifications.addNotificationResponseReceivedListener).mock.calls[0]![0];
  listener({notification: {request: {content: {data: {alertId: "alert", accountId: "account"}}}}} as never);
  listener({notification: {request: {content: {data: {alertId: 1}}}}} as never);
  expect(open).toHaveBeenCalledTimes(1);
  expect(open).toHaveBeenCalledWith("alert", "account");
  stop();
  expect(jest.mocked(Notifications.addNotificationResponseReceivedListener).mock.results[0]!.value.remove).toHaveBeenCalled();
});
