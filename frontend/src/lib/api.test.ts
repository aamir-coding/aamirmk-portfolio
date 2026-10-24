import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fetchHealth, getApiBaseUrl } from "./api";

describe("api client", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("resolves API base URL correctly", () => {
    expect(getApiBaseUrl()).toBeTruthy();
  });

  it("fetches and parses healthy status", async () => {
    const mockResponse = { status: "ok", ready: true };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    } as unknown as Response);

    const result = await fetchHealth();
    expect(result).toEqual({ status: "ok", ready: true });
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/health"),
      expect.objectContaining({ method: "GET" })
    );
  });

  it("throws descriptive error when response is not ok", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    } as unknown as Response);

    await expect(fetchHealth()).rejects.toThrow("Health check failed with HTTP 500");
  });

  it("throws error when response schema does not match", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ wrong: "data" }),
    } as unknown as Response);

    await expect(fetchHealth()).rejects.toThrow("Invalid response schema from health endpoint");
  });
});
