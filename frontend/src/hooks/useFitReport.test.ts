import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFitReport } from "./useFitReport";
import * as sseModule from "../lib/sse";
import * as apiModule from "../lib/api";
import type { FitReport } from "../lib/types";

describe("useFitReport hook", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(apiModule, "fetchFitPresets").mockResolvedValue([]);
  });

  it("clears preset identity when starting a custom submission", async () => {
    vi.spyOn(sseModule, "streamFitReport").mockImplementation(async (opts) => {
      opts.callbacks.onError("resting");
    });
    const {result} = renderHook(() => useFitReport());
    act(() => result.current.loadPreset({id:"a", title:"Preset A", company:"",
      match_expectation:"partial", text:"A".repeat(60)}));
    expect(result.current.activePreset?.id).toBe("a");
    await act(async () => { await result.current.submit("B".repeat(60), "Custom B"); });
    expect(result.current.activePreset).toBeNull();
  });

  it("initializes with idle state and null report", async () => {
    let hookResult: { current: ReturnType<typeof useFitReport> };
    await act(async () => {
      const { result } = renderHook(() => useFitReport());
      hookResult = result;
    });

    expect(hookResult!.current.status).toBe("idle");
    expect(hookResult!.current.report).toBeNull();
    expect(hookResult!.current.progress).toBeNull();
    expect(hookResult!.current.error).toBeNull();
  });

  it("rejects JD text shorter than 50 characters", async () => {
    let hookResult: { current: ReturnType<typeof useFitReport> };
    await act(async () => {
      const { result } = renderHook(() => useFitReport());
      hookResult = result;
    });

    await act(async () => {
      await hookResult!.current.submit("Too short JD text");
    });

    expect(hookResult!.current.status).toBe("error");
    expect(hookResult!.current.error).toContain("at least 50 characters");
    expect(hookResult!.current.report).toBeNull();
  });

  it("handles successful progress streaming and report completion", async () => {
    const mockReport: FitReport = {
      role_title: "Full-Stack AI Engineer",
      jd_hash: "b".repeat(64),
      score: {
        must_have_total: 2,
        must_have_strong: 2,
        must_have_partial: 0,
        must_have_gap: 0,
        nice_to_have_total: 0,
        nice_to_have_strong: 0,
        nice_to_have_partial: 0,
        nice_to_have_gap: 0,
        total_requirements: 2,
        overall_fit: "Strong Match",
        headline: "Covers 2 of 2 must-haves",
      },
      requirements: [],
      summary: "Excellent candidate fit for full-stack AI engineering.",
    };

    vi.spyOn(sseModule, "streamFitReport").mockImplementation(async (opts) => {
      opts.callbacks.onProgress({
        step: "retrieving",
        message: "Matching facts...",
        percent: 50,
      });
      opts.callbacks.onComplete(mockReport);
    });

    let hookResult: { current: ReturnType<typeof useFitReport> };
    await act(async () => {
      const { result } = renderHook(() => useFitReport());
      hookResult = result;
    });

    const validJd =
      "Looking for a Full-Stack AI Engineer with FastAPI and React experience " +
      "to build intelligent conversational applications.";

    await act(async () => {
      await hookResult!.current.submit(validJd, "Full-Stack AI Engineer");
    });

    expect(hookResult!.current.status).toBe("completed");
    expect(hookResult!.current.report).toEqual(mockReport);
    expect(hookResult!.current.error).toBeNull();
    expect(hookResult!.current.progress).toBeNull();
  });

  it("handles streaming error gracefully", async () => {
    vi.spyOn(sseModule, "streamFitReport").mockImplementation(async (opts) => {
      opts.callbacks.onError("Daily fit report quota exceeded.");
    });

    let hookResult: { current: ReturnType<typeof useFitReport> };
    await act(async () => {
      const { result } = renderHook(() => useFitReport());
      hookResult = result;
    });

    const validJd =
      "Looking for a Full-Stack AI Engineer with FastAPI and React experience " +
      "to build intelligent conversational applications.";

    await act(async () => {
      await hookResult!.current.submit(validJd);
    });

    expect(hookResult!.current.status).toBe("error");
    expect(hookResult!.current.error).toBe("Daily fit report quota exceeded.");
    expect(hookResult!.current.report).toBeNull();
  });

  it("resets state when reset is called", async () => {
    let hookResult: { current: ReturnType<typeof useFitReport> };
    await act(async () => {
      const { result } = renderHook(() => useFitReport());
      hookResult = result;
    });

    await act(async () => {
      await hookResult!.current.submit("short");
    });
    expect(hookResult!.current.status).toBe("error");

    act(() => {
      hookResult!.current.reset();
    });

    expect(hookResult!.current.status).toBe("idle");
  });
});

it("keeps cancelled fit usage unknown and ignores late callbacks", async () => {
  vi.restoreAllMocks();
  vi.spyOn(apiModule, "fetchFitPresets").mockResolvedValue([]);
  let captured: sseModule.StreamFitOptions | undefined;
  let finish: () => void = () => {};
  const pending = new Promise<void>((resolve) => { finish = resolve; });
  vi.spyOn(sseModule, "streamFitReport").mockImplementation(async (options) => {
    captured = options;
    await pending;
  });
  const { result } = renderHook(() => useFitReport());
  let work: Promise<void> | undefined;
  act(() => { work = result.current.submit("Synthetic portfolio job requirements. ".repeat(3)); });
  act(() => { result.current.abort(); captured?.callbacks.onError("Late error"); });
  await act(async () => { finish(); await work; });
  expect(result.current.status).toBe("idle");
  expect(result.current.errorReceipt?.delivery).toBe("cancelled");
  expect(result.current.errorReceipt?.telemetry).toBeUndefined();
  expect(result.current.error).toBeNull();
});
