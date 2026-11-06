import { afterEach, expect, it, vi } from "vitest";
import { getSessionId } from "./session";

afterEach(() => { vi.restoreAllMocks(); sessionStorage.clear(); });

it("keeps the same opaque identity across calls", () => {
  const first = getSessionId();
  expect(first).toMatch(/^[A-Za-z0-9_-]{1,64}$/);
  expect(getSessionId()).toBe(first);
});

it("replaces corrupt stored identities", () => {
  sessionStorage.setItem("amk_abuse_session_v1", "bad identifier with spaces");
  expect(getSessionId()).toMatch(/^[A-Za-z0-9_-]{1,64}$/);
});

it("remains usable and stable when storage is blocked", () => {
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw Error("blocked"); });
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw Error("blocked"); });
  const first = getSessionId();
  expect(getSessionId()).toBe(first);
});
