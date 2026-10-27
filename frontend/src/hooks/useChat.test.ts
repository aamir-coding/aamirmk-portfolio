import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useChat } from "./useChat";
import * as sseModule from "../lib/sse";

describe("useChat hook", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("initializes with empty message list and idle state", () => {
    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.conversationId).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("appends user and assistant messages and accumulates tokens", async () => {
    vi.spyOn(sseModule, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onToken("Aamir ");
      opts.callbacks.onToken("built ");
      opts.callbacks.onToken("this.");
      opts.callbacks.onDone({ conversation_id: "conv-123" });
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Tell me about Aamir");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]?.role).toBe("user");
    expect(result.current.messages[0]?.content).toBe("Tell me about Aamir");

    expect(result.current.messages[1]?.role).toBe("assistant");
    expect(result.current.messages[1]?.content).toBe("Aamir built this.");
    expect(result.current.messages[1]?.status).toBe("done");

    expect(result.current.conversationId).toBe("conv-123");
    expect(result.current.isStreaming).toBe(false);
  });

  it("handles streaming errors cleanly", async () => {
    vi.spyOn(sseModule, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onError("Rate limit reached");
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Hello");
    });

    expect(result.current.error).toBe("Rate limit reached");
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.messages[1]?.status).toBe("error");
  });

  it("ignores empty or whitespace messages", async () => {
    const spy = vi.spyOn(sseModule, "streamChat");
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("   ");
    });

    expect(spy).not.toHaveBeenCalled();
    expect(result.current.messages).toHaveLength(0);
  });

  it("stops streaming when stopStreaming is called", async () => {
    let capturedSignal: AbortSignal | undefined;
    vi.spyOn(sseModule, "streamChat").mockImplementation(async (opts) => {
      capturedSignal = opts.signal;
      opts.callbacks.onToken("Partial...");
      // Simulate long wait
      return new Promise((resolve) => setTimeout(resolve, 500));
    });

    const { result } = renderHook(() => useChat());

    act(() => {
      void result.current.sendMessage("Long query");
    });

    expect(result.current.isStreaming).toBe(true);

    act(() => {
      result.current.stopStreaming();
    });

    expect(capturedSignal?.aborted).toBe(true);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.messages[1]?.status).toBe("done");
  });
});
