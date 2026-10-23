import { AxiosError } from "axios";
import {
  http,
  request,
  setAccessToken,
  setUnauthorizedHandler,
} from "@/services/http";
import { ApiError } from "@/services/errors";

beforeEach(() => {
  setAccessToken(null);
  setUnauthorizedHandler(null);
});
const failure = (code: string, status?: number, data?: unknown) => {
  http.defaults.adapter = async (config) => {
    throw new AxiosError(
      "private transport diagnostic",
      code,
      config,
      undefined,
      status
        ? { status, data, statusText: "error", headers: {}, config }
        : undefined,
    );
  };
};
test("network failures have a user-facing message", async () => {
  failure("ERR_NETWORK");
  await expect(request("/health")).rejects.toMatchObject({
    code: "NETWORK_ERROR",
    status: null,
  });
});
test("timeouts and cancellation are distinguishable", async () => {
  failure("ECONNABORTED");
  await expect(request("/health")).rejects.toMatchObject({ code: "TIMEOUT" });
  failure("ERR_CANCELED");
  await expect(request("/health")).rejects.toMatchObject({ code: "CANCELLED" });
});
test("validation preserves the safe API message and request identifier", async () => {
  failure("ERR_BAD_REQUEST", 422, {
    error: {
      code: "VALIDATION_ERROR",
      message: "Confira os campos.",
      details: [],
    },
    request_id: "demo-id",
  });
  await expect(request("/auth/login")).rejects.toMatchObject({
    code: "VALIDATION_ERROR",
    status: 422,
    requestId: "demo-id",
  });
});
test("server diagnostics are not exposed when no structured response is returned", async () => {
  failure("ERR_BAD_RESPONSE", 500, "<html>private SQL diagnostic</html>");
  try {
    await request("/health");
  } catch (error) {
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).not.toContain("private");
  }
});
test("expired sessions are cleared, invalid login does not clear another session", async () => {
  const clear = jest.fn();
  setUnauthorizedHandler(clear);
  failure("ERR_BAD_REQUEST", 401);
  await expect(request("/auth/me")).rejects.toMatchObject({ status: 401 });
  expect(clear).toHaveBeenCalledTimes(1);
  await expect(request("/auth/login")).rejects.toMatchObject({ status: 401 });
  expect(clear).toHaveBeenCalledTimes(1);
});
test("relative paths cannot switch the configured API host", async () => {
  await expect(request("//other.example")).rejects.toThrow("caminho relativo");
});
