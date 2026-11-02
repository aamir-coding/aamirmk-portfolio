import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ChatInput } from "./ChatInput";

describe("<ChatInput />", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders textarea, send button, and keyboard shortcut badge", () => {
    render(<ChatInput onSend={vi.fn()} onStop={vi.fn()} isStreaming={false} />);

    expect(
      screen.getByPlaceholderText(/Ask about Aamir's experience/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Send message/i })).toBeInTheDocument();
    expect(screen.getByText("Ctrl+K")).toBeInTheDocument();
  });

  it("focuses textarea when Ctrl+K or Cmd+K is pressed globally", () => {
    render(<ChatInput onSend={vi.fn()} onStop={vi.fn()} isStreaming={false} />);
    const textarea = screen.getByPlaceholderText(/Ask about Aamir's experience/i);

    expect(document.activeElement).toBe(textarea);

    // Blur it
    textarea.blur();
    expect(document.activeElement).not.toBe(textarea);

    // Fire Ctrl+K globally on window
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(document.activeElement).toBe(textarea);
  });

  it("calls onSend with trimmed text when Enter is pressed without Shift", () => {
    const handleSend = vi.fn();
    render(<ChatInput onSend={handleSend} onStop={vi.fn()} isStreaming={false} />);
    const textarea = screen.getByPlaceholderText(/Ask about Aamir's experience/i);

    fireEvent.change(textarea, { target: { value: "Tell me about Redis" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(handleSend).toHaveBeenCalledWith("Tell me about Redis");
    expect(textarea).toHaveValue("");
  });

  it("calls onStop when Escape is pressed while streaming", () => {
    const handleStop = vi.fn();
    render(<ChatInput onSend={vi.fn()} onStop={handleStop} isStreaming={true} />);
    const textarea = screen.getByPlaceholderText(/Assistant dispatch in progress/i);

    fireEvent.keyDown(textarea, { key: "Escape" });
    expect(handleStop).toHaveBeenCalled();
  });
});
