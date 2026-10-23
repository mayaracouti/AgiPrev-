import { useAuth } from "@/auth/AuthProvider";
import {
  createContext,
  useContext,
  useReducer,
  useRef,
  useEffect,
  type ReactNode,
  type Dispatch,
} from "react";
import {
  balanceOf,
  demoReducer,
  initialState,
  validateTransaction,
} from "./model";
import type { DemoState, Transaction, Action } from "./types";

interface DemoContextValue {
  state: DemoState;
  signedIn: boolean;
  signOut: () => Promise<void>;
  dispatch: Dispatch<Action>;
  confirm: (transaction: Transaction) => string | null;
  balance: number;
}
const DemoContext = createContext<DemoContextValue | null>(null);
export function DemoProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(demoReducer, undefined, () =>
    initialState(),
  );
  const auth = useAuth();
  const signedIn = auth.session !== null;
  const guard = useRef(new Set<string>());
  useEffect(() => {
    if (auth.session) {
      guard.current.clear();
      dispatch({ type: "reset", profileId: auth.session.customer.demo_profile, seed: 42 });
    }
  }, [auth.session]);
  function confirm(transaction: Transaction) {
    const error = validateTransaction(state, transaction);
    if (error) return error;
    if (guard.current.has(transaction.id))
      return "Esta movimentação já foi confirmada.";
    guard.current.add(transaction.id);
    dispatch({ type: "transaction", transaction });
    return null;
  }
  return (
    <DemoContext.Provider
      value={{
        state,
        dispatch,
        signedIn,
        signOut: auth.logout,
        confirm,
        balance: balanceOf(state),
      }}
    >
      {children}
    </DemoContext.Provider>
  );
}
export function useDemo() {
  const value = useContext(DemoContext);
  if (!value) throw new Error("DemoProvider ausente");
  return value;
}
