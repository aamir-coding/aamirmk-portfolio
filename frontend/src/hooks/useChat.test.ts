import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useChat, CHAT_SESSION_STORAGE_KEY } from "./useChat";
import * as sseModule from "../lib/sse";

describe("useChat hook", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  it("initializes with empty message list and idle state when storage is empty", () => {
    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.conversationId).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("hydrates previous conversation from sessionStorage on mount", () => {
    const saved = {
      messages: [
        {
          id: "u-1",
          role: "user",
          content: "Previous query",
          status: "done",
          timestamp: "12:00 PM",
        },
        {
          id: "a-1",
          role: "assistant",
          content: "Previous answer",
          status: "done",
          timestamp: "12:00 PM",
        },
      ],
      conversationId: "saved-conv-456",
    };
    sessionStorage.setItem(CHAT_SESSION_STORAGE_KEY, JSON.stringify(saved));

    const { result } = renderHook(() => useChat());
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]?.content).toBe("Previous query");
    expect(result.current.conversationId).toBe("saved-conv-456");
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

    // Verify persisted to sessionStorage
    const stored = JSON.parse(
      sessionStorage.getItem(CHAT_SESSION_STORAGE_KEY) || "{}"
    );
    expect(stored.messages).toHaveLength(2);
    expect(stored.conversationId).toBe("conv-123");
  });

  it("supports sendInstantAnswer for 0ms cold-start offline responses", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendInstantAnswer("What is Aamir's experience?", {
        reply: "Instant offline dossier answer.",
        sources: [
          {
            chunk_id: "test-chunk",
            title: "Test Receipt",
            type: "skill",
            source_section: "S1",
          },
        ],
      });
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]?.content).toBe("What is Aamir's experience?");
    expect(result.current.messages[1]?.content).toBe("Instant offline dossier answer.");
    expect(result.current.messages[1]?.sources).toHaveLength(1);
    expect(result.current.isStreaming).toBe(false);

    const stored = JSON.parse(
      sessionStorage.getItem(CHAT_SESSION_STORAGE_KEY) || "{}"
    );
    expect(stored.messages).toHaveLength(2);
  });

  it("clears messages and sessionStorage on resetChat", () => {
    const { result } = renderHook(() => useChat());

    act(() => {
      result.current.sendInstantAnswer("Question", { reply: "Answer" });
    });
    expect(result.current.messages).toHaveLength(2);
    expect(sessionStorage.getItem(CHAT_SESSION_STORAGE_KEY)).not.toBeNull();

    act(() => {
      result.current.resetChat();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(sessionStorage.getItem(CHAT_SESSION_STORAGE_KEY)).toBeNull();
  });

  it("handles streaming errors cleanly with inline error content", async () => {
    vi.spyOn(sseModule, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onError(
        "Rate limit reached. Please wait 15 seconds before sending another message."
      );
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Hello");
    });

    expect(result.current.error).toBe(
      "Rate limit reached. Please wait 15 seconds before sending another message."
    );
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.messages[1]?.status).toBe("error");
    expect(result.current.messages[1]?.content).toBe(
      "Rate limit reached. Please wait 15 seconds before sending another message."
    );
  });

  it("handles daily quota exhaustion cleanly", async () => {
    vi.spyOn(sseModule, "streamChat").mockImplementation(async (opts) => {
      opts.callbacks.onError(
        "Daily assistant conversation capacity reached. Feel free to connect directly with Aamir."
      );
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage("Hello");
    });

    expect(result.current.error).toContain(
      "Daily assistant conversation capacity reached"
    );
    expect(result.current.messages[1]?.status).toBe("error");
    expect(result.current.messages[1]?.content).toContain(
      "connect directly with Aamir"
    );
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
