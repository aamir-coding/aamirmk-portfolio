import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useChat } from "./useChat";
import { useFitReport } from "./useFitReport";

afterEach(() => {
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

function closedResponse(payload = "") {
  return { ok: true, body: new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(payload));
      controller.close();
    },
  }) };
}

it("chat recovers from truncated transport and permits a successful retry", async () => {
  vi.stubGlobal("fetch", vi.fn()
    .mockResolvedValueOnce(closedResponse())
    .mockResolvedValueOnce(closedResponse('event: done\ndata: {"conversation_id":"retry"}\n\n')));
  const { result } = renderHook(() => useChat());
  await act(async () => { await result.current.sendMessage("First attempt"); });
  expect(result.current.isStreaming).toBe(false);
  expect(result.current.error).toMatch(/ended before completion/i);
  expect(result.current.messages.at(-1)?.status).toBe("error");
  await act(async () => { await result.current.sendMessage("Try again"); });
  expect(result.current.isStreaming).toBe(false);
  expect(result.current.error).toBeNull();
  expect(result.current.conversationId).toBe("retry");
});

it("fit leaves streaming on EOF and can start another request", async () => {
  const fetchMock = vi.fn().mockImplementation(async (url: string) =>
    url.endsWith("/presets") ? { ok: true, json: async () => [] } : closedResponse());
  vi.stubGlobal("fetch", fetchMock);
  const { result } = renderHook(() => useFitReport());
  await waitFor(() => expect(result.current.isLoadingPresets).toBe(false));
  await act(async () => { await result.current.submit("A".repeat(60)); });
  expect(result.current.status).toBe("error");
  expect(result.current.error).toMatch(/ended before completion/i);
  await act(async () => { await result.current.submit("B".repeat(60)); });
  expect(fetchMock.mock.calls.filter(([url]) => String(url).endsWith("/fit"))).toHaveLength(2);
  expect(result.current.status).toBe("error");
});
