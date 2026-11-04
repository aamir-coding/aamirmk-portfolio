import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import {
  CardEventPayloadSchema,
  DoneEventPayloadSchema,
  ErrorEventPayloadSchema,
  FitErrorPayloadSchema,
  FitProgressDataSchema,
  FitReportSchema,
  SourcesEventPayloadSchema,
  TokenEventPayloadSchema,
} from "./contracts";
import { parseSSEBuffer, streamChat, streamFitReport } from "./sse";

const fixtureSchema = z.object({
  schema_version: z.literal(1),
  purpose: z.literal("fake_and_curated_endpoint_captures"),
  records: z.array(z.object({
    id: z.string(),
    origin: z.enum(["fake", "curated"]),
    transport: z.enum(["chat_sse", "fit_sse", "preset_json"]),
    raw_sse: z.string(),
    preset_report: z.unknown().nullable(),
  })),
});

const fixturePath = resolve(process.cwd(), "../evals/recordings/endpoints-v1.json");
const fixtures = fixtureSchema.parse(JSON.parse(readFileSync(fixturePath, "utf8"))).records;

function capture(id: string) {
  const found = fixtures.find((record) => record.id === id);
  if (!found) throw new Error(`Missing backend fixture: ${id}`);
  return found;
}

function responseBody(raw: string, width = 7): ReadableStream<Uint8Array> {
  const bytes = new TextEncoder().encode(raw);
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (let i = 0; i < bytes.length; i += width) controller.enqueue(bytes.slice(i, i + width));
      controller.close();
    },
  });
}

function mockResponse(raw: string, width = 7): ReadableStream<Uint8Array> {
  const body = responseBody(raw, width);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(body, { status: 200 })));
  return body;
}

afterEach(() => vi.unstubAllGlobals());

describe("actual FastAPI captures satisfy frontend contracts", () => {
  it.each(fixtures)("validates every response payload in $id ($origin)", (record) => {
    if (record.transport === "preset_json") {
      expect(FitReportSchema.safeParse(record.preset_report).success).toBe(true);
      return;
    }
    const { events, remaining } = parseSSEBuffer(record.raw_sse);
    expect(remaining).toBe("");
    expect(events.length).toBeGreaterThan(0);
    for (const event of events) {
      const schema = record.transport === "chat_sse"
        ? { sources: SourcesEventPayloadSchema, card: CardEventPayloadSchema, token: TokenEventPayloadSchema, done: DoneEventPayloadSchema, error: ErrorEventPayloadSchema }[event.event as "sources" | "card" | "token" | "done" | "error"]
        : { progress: FitProgressDataSchema, complete: FitReportSchema, error: FitErrorPayloadSchema }[event.event as "progress" | "complete" | "error"];
      if (!schema) throw new Error(`Unexpected event: ${event.event}`);
      const payload: unknown = JSON.parse(event.data);
      expect(schema.safeParse(payload).success).toBe(true);
    }
  });

  it.each([1, 7])("replays chat tokens/cards through real transport at %i-byte boundaries", async (width) => {
    const record = capture("chat-project");
    const body = mockResponse(record.raw_sse, width);
    const onDone = vi.fn();
    const onError = vi.fn();
    const onCard = vi.fn();
    const onSources = vi.fn();
    let text = "";
    await streamChat({
      message: "Fixture replay",
      callbacks: { onToken: (token) => { text += token; }, onDone, onError, onCard, onSources },
    });
    const expected = parseSSEBuffer(record.raw_sse).events
      .filter((event) => event.event === "token")
      .map((event) => TokenEventPayloadSchema.parse(JSON.parse(event.data)).token).join("");
    expect(text).toBe(expected);
    expect(text).toContain("Aamir:");
    expect(text).toContain("—");
    expect(onDone).toHaveBeenCalledTimes(1);
    expect(onCard).toHaveBeenCalledTimes(1);
    expect(onSources).toHaveBeenCalledTimes(1);
    expect(onError).not.toHaveBeenCalled();
    expect(body.locked).toBe(false);
  });

  it.each(["fit-fresh", "fit-cached"])("replays %s through the real fit client", async (id) => {
    const body = mockResponse(capture(id).raw_sse);
    const onComplete = vi.fn();
    const onError = vi.fn();
    const onProgress = vi.fn();
    await streamFitReport({ jdText: "Fixture replay", callbacks: { onComplete, onError, onProgress } });
    expect(onComplete).toHaveBeenCalledTimes(1);
    expect(onProgress).toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
    expect(body.locked).toBe(false);
  });

  it.each(["chat-error", "fit-extraction-error"])("handles captured application error %s once", async (id) => {
    const record = capture(id);
    const body = mockResponse(record.raw_sse);
    const onError = vi.fn();
    const onComplete = vi.fn();
    if (record.transport === "chat_sse") {
      await streamChat({ message: "Fixture replay", callbacks: { onToken: vi.fn(), onDone: onComplete, onError } });
    } else {
      await streamFitReport({ jdText: "Fixture replay", callbacks: { onProgress: vi.fn(), onComplete, onError } });
    }
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onComplete).not.toHaveBeenCalled();
    expect(body.locked).toBe(false);
  });

  it.each([
    ["chat-project", "done"], ["fit-fresh", "complete"],
  ])("rejects premature EOF after captured %s progress/tokens", async (id, terminal) => {
    const record = capture(id);
    const raw = record.raw_sse.slice(0, record.raw_sse.lastIndexOf(`event: ${terminal}`));
    const body = mockResponse(raw);
    const onError = vi.fn();
    const onComplete = vi.fn();
    if (record.transport === "chat_sse") {
      await streamChat({ message: "Fixture replay", callbacks: { onToken: vi.fn(), onDone: onComplete, onError } });
    } else {
      await streamFitReport({ jdText: "Fixture replay", callbacks: { onProgress: vi.fn(), onComplete, onError } });
    }
    expect(onError).toHaveBeenCalledExactlyOnceWith(expect.stringMatching(/ended.*complet/i));
    expect(onComplete).not.toHaveBeenCalled();
    expect(body.locked).toBe(false);
  });

  it.each([
    ["chat-project", "done"], ["fit-fresh", "complete"],
  ])("rejects corrupted terminal JSON after captured %s", async (id, terminal) => {
    const record = capture(id);
    const prefix = record.raw_sse.slice(0, record.raw_sse.lastIndexOf(`event: ${terminal}`));
    const body = mockResponse(`${prefix}event: ${terminal}\ndata: not JSON\n\n`);
    const onError = vi.fn();
    const onComplete = vi.fn();
    if (record.transport === "chat_sse") {
      await streamChat({ message: "Fixture replay", callbacks: { onToken: vi.fn(), onDone: onComplete, onError } });
    } else {
      await streamFitReport({ jdText: "Fixture replay", callbacks: { onProgress: vi.fn(), onComplete, onError } });
    }
    expect(onError).toHaveBeenCalledTimes(1);
    expect(onComplete).not.toHaveBeenCalled();
    expect(body.locked).toBe(false);
  });
});
