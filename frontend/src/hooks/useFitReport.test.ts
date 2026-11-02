import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFitReport } from "./useFitReport";
import * as sseModule from "../lib/sse";
import type { FitReport } from "../lib/types";

describe("useFitReport hook", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("initializes with idle state and null report", () => {
    const { result } = renderHook(() => useFitReport());
    expect(result.current.status).toBe("idle");
    expect(result.current.report).toBeNull();
    expect(result.current.progress).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("rejects JD text shorter than 50 characters", async () => {
    const { result } = renderHook(() => useFitReport());

    await act(async () => {
      await result.current.submit("Too short JD text");
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toContain("at least 50 characters");
    expect(result.current.report).toBeNull();
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

    const { result } = renderHook(() => useFitReport());

    const validJd =
      "Looking for a Full-Stack AI Engineer with FastAPI and React experience " +
      "to build intelligent conversational applications.";

    await act(async () => {
      await result.current.submit(validJd, "Full-Stack AI Engineer");
    });

    expect(result.current.status).toBe("completed");
    expect(result.current.report).toEqual(mockReport);
    expect(result.current.error).toBeNull();
    expect(result.current.progress).toBeNull();
  });

  it("handles streaming error gracefully", async () => {
    vi.spyOn(sseModule, "streamFitReport").mockImplementation(async (opts) => {
      opts.callbacks.onError("Daily fit report quota exceeded.");
    });

    const { result } = renderHook(() => useFitReport());

    const validJd =
      "Looking for a Full-Stack AI Engineer with FastAPI and React experience " +
      "to build intelligent conversational applications.";

    await act(async () => {
      await result.current.submit(validJd);
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error).toBe("Daily fit report quota exceeded.");
    expect(result.current.report).toBeNull();
  });

  it("resets state when reset is called", async () => {
    const { result } = renderHook(() => useFitReport());

    await act(async () => {
      await result.current.submit("short");
    });
    expect(result.current.status).toBe("error");

    act(() => {
      result.current.reset();
    });

    expect(result.current.status).toBe("idle");
    expect(result.current.error).toBeNull();
    expect(result.current.report).toBeNull();
  });
});
