import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";
import { useTheme } from "./useTheme";

describe("useTheme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("defaults to system theme when no stored preference exists", () => {
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("system");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("allows setting dark theme explicitly and updates document attribute", () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.setTheme("dark");
    });

    expect(result.current.theme).toBe("dark");
    expect(result.current.resolvedTheme).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(localStorage.getItem("amk_portfolio_theme")).toBe("dark");
  });

  it("allows setting light theme explicitly and updates document attribute", () => {
    const { result } = renderHook(() => useTheme());

    act(() => {
      result.current.setTheme("light");
    });

    expect(result.current.theme).toBe("light");
    expect(result.current.resolvedTheme).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(localStorage.getItem("amk_portfolio_theme")).toBe("light");
  });

  it("cycles theme through system -> dark -> light -> system", () => {
    const { result } = renderHook(() => useTheme());

    expect(result.current.theme).toBe("system");

    act(() => {
      result.current.cycleTheme();
    });
    expect(result.current.theme).toBe("dark");

    act(() => {
      result.current.cycleTheme();
    });
    expect(result.current.theme).toBe("light");

    act(() => {
      result.current.cycleTheme();
    });
    expect(result.current.theme).toBe("system");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("initializes from valid localStorage value", () => {
    localStorage.setItem("amk_portfolio_theme", "dark");
    const { result } = renderHook(() => useTheme());
    expect(result.current.theme).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });
});
