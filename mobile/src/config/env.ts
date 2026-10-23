import { validateApiUrl } from "./validateEnv";
export const env = {
  apiUrl: validateApiUrl(process.env.EXPO_PUBLIC_API_URL),
} as const;
