import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  request,
  setAccessToken,
  setUnauthorizedHandler,
} from "@/services/http";
import type { Customer, LoginResponse } from "@/features/banking/contracts";
import { ApiError, errorMessage } from "@/services/errors";

interface CustomerQuery { profile?: string; search?: string; offset?: number }
interface AuthContextValue {
  session: LoginResponse | null;
  customers: Customer[];
  loading: boolean;
  error: string | null;
  loadCustomers: (query?: CustomerQuery) => Promise<void>;
  login: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}
const AuthContext = createContext<AuthContextValue | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<LoginResponse | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);
  const customerRequest = useRef(0);
  const clear = useCallback(() => {
    setAccessToken(null);
    setSession(null);
  }, []);
  useEffect(() => {
    setUnauthorizedHandler(clear);
    return () => setUnauthorizedHandler(null);
  }, [clear]);
  useEffect(() => {
    if (!session) return;
    const timer = setTimeout(
      clear,
      Math.max(0, Date.parse(session.expires_at) - Date.now()),
    );
    return () => clearTimeout(timer);
  }, [session, clear]);
  const loadCustomers = useCallback(async (query: CustomerQuery = {}) => {
    const current = ++customerRequest.current;
    setCustomers([]);
    setLoading(true);
    setError(null);
    try {
      const data = await request<Customer[]>("/customers", {params: {...query, limit: 50}});
      if (!Array.isArray(data)) throw new Error("Invalid profiles");
      if (current === customerRequest.current) setCustomers(data);
    } catch (cause) {
      if (current === customerRequest.current) setError(errorMessage(cause));
    } finally {
      if (current === customerRequest.current) setLoading(false);
    }
  }, []);
  async function login(email: string) {
    if (inFlight.current) return;
    inFlight.current = true;
    setLoading(true);
    setError(null);
    try {
      const data = await request<LoginResponse>("/auth/login", {
        method: "POST",
        data: { email },
      });
      if (
        !data.access_token ||
        !data.accounts?.length ||
        !Number.isFinite(Date.parse(data.expires_at))
      )
        throw new ApiError(
          null,
          "INVALID_RESPONSE",
          "A API retornou uma sessão incompleta.",
        );
      setAccessToken(data.access_token);
      setSession(data);
    } catch (cause) {
      setError(errorMessage(cause));
      throw cause;
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }
  async function logout() {
    // A server failure is not silently reported as a successfully revoked session.
    await request<void>("/auth/logout", { method: "POST" });
    clear();
  }
  return (
    <AuthContext.Provider
      value={{
        session,
        customers,
        loading,
        error,
        loadCustomers,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  const auth = useContext(AuthContext);
  if (!auth) throw new Error("AuthProvider ausente");
  return auth;
}
