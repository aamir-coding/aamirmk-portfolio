import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useServerHealth } from "./useServerHealth";

describe("server health lifecycle", () => {
  beforeEach(() => { vi.useFakeTimers(); });
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

  it("bounds a hung health check and allows explicit recovery", async () => {
    let signal: AbortSignal | undefined;
    const fetchMock = vi.fn().mockImplementation((_url: string, init: RequestInit) => {
      signal = init.signal ?? undefined;
      return new Promise<Response>(() => {});
    });
    vi.stubGlobal("fetch", fetchMock);
    const { result } = renderHook(() => useServerHealth());
    await act(() => vi.advanceTimersByTimeAsync(2500));
    expect(result.current.state).toBe("warming");
    await act(() => vi.advanceTimersByTimeAsync(87500));
    expect(result.current.state).toBe("error");
    expect(signal?.aborted).toBe(true);
    fetchMock.mockResolvedValue(new Response(JSON.stringify({status:"ok",ready:true,assistant_state:"resting"})));
    await act(async () => result.current.refresh());
    expect(result.current.state).toBe("resting");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("requires explicit ready capacity and does not overwrite after unmount", async () => {
    let resolve: (value: Response) => void = () => {};
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(r => { resolve = r; })));
    const { result, unmount } = renderHook(() => useServerHealth());
    await act(async () => resolve(new Response(JSON.stringify({status:"ok",ready:true}))));
    expect(result.current.state).toBe("resting");
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });

  it("does not report unready HTTP 200 responses as ready", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({status:"unavailable",ready:false,assistant_state:"ready"}))));
    const { result } = renderHook(() => useServerHealth());
    await act(async () => {});
    expect(result.current.state).toBe("error");
  });
});
