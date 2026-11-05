import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, expect, it, vi } from "vitest";
import { z } from "zod";
import { DoneEventPayloadSchema, FitReportSchema, RequestTelemetrySchema } from "./contracts";
import { parseSSEBuffer, streamChat } from "./sse";

const captures = z.object({ records: z.array(z.object({
  id: z.string(), raw_sse: z.string(),
})) }).parse(JSON.parse(readFileSync(resolve(process.cwd(),
  "../evals/recordings/endpoints-v2-telemetry.json"), "utf8"))).records;

afterEach(() => vi.unstubAllGlobals());

it.each(captures.filter((r) => r.id !== "fit-preset"))(
  "validates actual backend telemetry in $id", (record) => {
    const frames = parseSSEBuffer(record.raw_sse).events;
    const terminal = frames.at(-1);
    expect(terminal).toBeDefined();
    const payload = JSON.parse(terminal!.data) as unknown;
    if (terminal!.event === "complete") expect(FitReportSchema.parse(payload).telemetry).toBeDefined();
    if (terminal!.event === "done") expect(DoneEventPayloadSchema.parse(payload).telemetry).toBeDefined();
    if (record.id !== "chat-error") {
      const telemetry = RequestTelemetrySchema.parse(z.object({ telemetry: z.unknown() }).parse(payload).telemetry);
      expect(telemetry.total_ms).toBe(0); // Injected capture clock, never model performance.
      if (record.id === "fit-cached") expect(telemetry.origin).toBe("cache");
    }
  },
);

it("keeps server and browser timings separate through real SSE parsing", async () => {
  const record = captures.find((r) => r.id === "chat-project")!;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(record.raw_sse)));
  const onDone = vi.fn();
  const onError = vi.fn();
  await streamChat({ message: "offline replay", callbacks: { onDone, onError, onToken: vi.fn() } });
  expect(onError).not.toHaveBeenCalled();
  const payload = onDone.mock.calls[0][0] as { telemetry: { total_ms: number; usage_complete: boolean }; browserTiming: { total_ms: number } };
  expect(payload.telemetry.total_ms).toBe(0);
  expect(payload.telemetry.usage_complete).toBe(false);
  expect(payload.browserTiming.total_ms).toBeGreaterThanOrEqual(0);
});
