import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { parseSSEBuffer, streamChat } from "./sse";

describe("parseSSEBuffer", () => {
  it("parses single complete SSE event", () => {
    const raw = 'event: token\ndata: {"token": "hello"}\n\n';
    const { events, remaining } = parseSSEBuffer(raw);

    expect(events).toEqual([
      { event: "token", data: '{"token": "hello"}' },
    ]);
    expect(remaining).toBe("");
  });

  it("handles multiple events in one chunk", () => {
    const raw =
      'event: token\ndata: {"token": "hello"}\n\nevent: token\ndata: {"token": " world"}\n\n';
    const { events, remaining } = parseSSEBuffer(raw);

    expect(events).toHaveLength(2);
    expect(events[0]).toEqual({ event: "token", data: '{"token": "hello"}' });
    expect(events[1]).toEqual({ event: "token", data: '{"token": " world"}' });
    expect(remaining).toBe("");
  });

  it("retains partial trailing events in remaining buffer", () => {
    const raw =
      'event: token\ndata: {"token": "first"}\n\nevent: token\ndata: {"token": "par';
    const { events, remaining } = parseSSEBuffer(raw);

    expect(events).toHaveLength(1);
    expect(events[0]?.data).toBe('{"token": "first"}');
    expect(remaining).toBe('event: token\ndata: {"token": "par');
  });

  it("handles empty or whitespace strings", () => {
    const { events, remaining } = parseSSEBuffer("");
    expect(events).toHaveLength(0);
    expect(remaining).toBe("");
  });
});

describe("streamChat", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it("streams tokens and signals completion", async () => {
    const ssePayload =
      'event: token\ndata: {"token": "Hi"}\n\n' +
      'event: token\ndata: {"token": " there"}\n\n' +
      'event: done\ndata: {"conversation_id": "test-c1"}\n\n';

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(ssePayload));
        controller.close();
      },
    });

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    } as unknown as Response);

    const tokens: string[] = [];
    let doneConvId = "";
    let errorReceived = "";

    await streamChat({
      message: "Hello",
      baseUrl: "http://localhost:8000",
      callbacks: {
        onToken: (t) => tokens.push(t),
        onDone: (d) => {
          doneConvId = d.conversation_id;
        },
        onError: (e) => {
          errorReceived = e;
        },
      },
    });

    expect(tokens).toEqual(["Hi", " there"]);
    expect(doneConvId).toBe("test-c1");
    expect(errorReceived).toBe("");
  });

  it("calls onError on non-200 HTTP response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        error: { message: "Validation error: message cannot be empty" },
      }),
    } as unknown as Response);

    let errorReceived = "";
    await streamChat({
      message: "",
      baseUrl: "http://localhost:8000",
      callbacks: {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: (e) => {
          errorReceived = e;
        },
      },
    });

    expect(errorReceived).toContain("Validation error");
  });

  it("calls onError when stream contains event: error", async () => {
    const ssePayload =
      'event: error\ndata: {"detail": "Rate limit exceeded"}\n\n';

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(ssePayload));
        controller.close();
      },
    });

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    } as unknown as Response);

    let errorReceived = "";
    await streamChat({
      message: "Hello",
      baseUrl: "http://localhost:8000",
      callbacks: {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError: (e) => {
          errorReceived = e;
        },
      },
    });

    expect(errorReceived).toBe("Rate limit exceeded");
  });

  it("handles abort signal cleanly without calling onError", async () => {
    const controller = new AbortController();

    globalThis.fetch = vi.fn().mockImplementation(() => {
      controller.abort();
      const err = new Error("The operation was aborted");
      err.name = "AbortError";
      throw err;
    });

    const onError = vi.fn();
    await streamChat({
      message: "Hello",
      signal: controller.signal,
      baseUrl: "http://localhost:8000",
      callbacks: {
        onToken: vi.fn(),
        onDone: vi.fn(),
        onError,
      },
    });

    expect(onError).not.toHaveBeenCalled();
  });

  it("dispatches onSources and onCard callbacks when received in stream", async () => {
    const ssePayload =
      'event: sources\ndata: {"sources": [{"chunk_id": "c1", "title": "Entropy OJ", "type": "project", "source_section": "J1", "source_url": "https://entropy-oj.vercel.app"}]}\n\n' +
      'event: card\ndata: {"card": {"id": "entropy-oj", "title": "Entropy Online Judge", "subtitle": "DSA Platform", "summary": "Platform", "role": "Author", "tech_stack": ["React"], "highlights": ["Async"], "metrics": {}, "source_sections": ["J1"], "architecture_details": "Arch"}}\n\n' +
      'event: token\ndata: {"token": "Overview"}\n\n' +
      'event: done\ndata: {"conversation_id": "conv-1"}\n\n';

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode(ssePayload));
        controller.close();
      },
    });

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: stream,
    } as unknown as Response);

    const onSources = vi.fn();
    const onCard = vi.fn();
    const onToken = vi.fn();
    const onDone = vi.fn();

    await streamChat({
      message: "Entropy",
      callbacks: {
        onSources,
        onCard,
        onToken,
        onDone,
        onError: vi.fn(),
      },
    });

    expect(onSources).toHaveBeenCalledWith([
      {
        chunk_id: "c1",
        title: "Entropy OJ",
        type: "project",
        source_section: "J1",
        source_url: "https://entropy-oj.vercel.app",
      },
    ]);
    expect(onCard).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "entropy-oj",
        title: "Entropy Online Judge",
      })
    );
    expect(onToken).toHaveBeenCalledWith("Overview");
    expect(onDone).toHaveBeenCalledWith({ conversation_id: "conv-1" });
  });
});
