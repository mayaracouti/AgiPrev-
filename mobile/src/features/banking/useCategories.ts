import { useEffect, useState } from "react";
import { request } from "@/services/http";
import { errorMessage } from "@/services/errors";
import type { Category } from "./contracts";
export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    void request<Category[]>("/categories", {signal: controller.signal}).then(setCategories)
      .catch((cause) => {if (!controller.signal.aborted) setError(errorMessage(cause));});
    return () => controller.abort();
  }, []);
  return {categories, error};
}
