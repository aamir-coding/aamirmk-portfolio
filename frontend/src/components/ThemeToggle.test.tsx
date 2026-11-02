import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ThemeToggle } from "./ThemeToggle";

describe("ThemeToggle", () => {
  it("renders system theme with resolved mode indicator", () => {
    const handleCycle = vi.fn();
    render(
      <ThemeToggle
        theme="system"
        resolvedTheme="light"
        onCycle={handleCycle}
      />
    );

    const button = screen.getByRole("button", {
      name: /Current theme is system, showing light mode/i,
    });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("Theme: Auto (light)");
    expect(button).toHaveTextContent("◐");
  });

  it("renders dark theme correctly", () => {
    const handleCycle = vi.fn();
    render(
      <ThemeToggle
        theme="dark"
        resolvedTheme="dark"
        onCycle={handleCycle}
      />
    );

    const button = screen.getByRole("button", {
      name: /Current theme is dark, showing dark mode/i,
    });
    expect(button).toHaveTextContent("Theme: Dark");
    expect(button).toHaveTextContent("☾");
  });

  it("renders light theme correctly", () => {
    const handleCycle = vi.fn();
    render(
      <ThemeToggle
        theme="light"
        resolvedTheme="light"
        onCycle={handleCycle}
      />
    );

    const button = screen.getByRole("button", {
      name: /Current theme is light, showing light mode/i,
    });
    expect(button).toHaveTextContent("Theme: Light");
    expect(button).toHaveTextContent("☼");
  });

  it("calls onCycle when clicked", () => {
    const handleCycle = vi.fn();
    render(
      <ThemeToggle
        theme="system"
        resolvedTheme="light"
        onCycle={handleCycle}
      />
    );

    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(handleCycle).toHaveBeenCalledTimes(1);
  });
});
