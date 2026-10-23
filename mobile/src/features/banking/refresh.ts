import { useSyncExternalStore } from "react";
let version = 0;
const listeners = new Set<() => void>();
export function bankingUpdated() {
  version += 1;
  listeners.forEach((listener) => listener());
}
const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
};
export const useBankingVersion = () => useSyncExternalStore(subscribe, () => version, () => version);
