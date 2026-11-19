import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, createEvent, fireEvent } from "@testing-library/react";
import { ChatInput } from "./ChatInput";

describe("<ChatInput />", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders textarea, send button, and keyboard shortcut badge", () => {
    render(<ChatInput onSend={vi.fn()} onStop={vi.fn()} isStreaming={false} />);

    expect(
      screen.getByRole("textbox", { name: /Ask a question about Aamir/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask a question" })).toBeInTheDocument();
    expect(screen.getByText("Ctrl+K")).toBeInTheDocument();
  });

  it("focuses textarea when Ctrl+K or Cmd+K is pressed globally", () => {
    render(<ChatInput onSend={vi.fn()} onStop={vi.fn()} isStreaming={false} />);
    const textarea = screen.getByRole("textbox", { name: /Ask a question about Aamir/i });

    expect(textarea).not.toHaveFocus();

    // Fire Ctrl+K globally on window
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(document.activeElement).toBe(textarea);
  });

  it("calls onSend with trimmed text when Enter is pressed without Shift", () => {
    const handleSend = vi.fn();
    render(<ChatInput onSend={handleSend} onStop={vi.fn()} isStreaming={false} />);
    const textarea = screen.getByRole("textbox", { name: /Ask a question about Aamir/i });

    fireEvent.change(textarea, { target: { value: "Tell me about Redis" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(handleSend).toHaveBeenCalledWith("Tell me about Redis");
    expect(textarea).toHaveValue("");
  });

  it("calls onStop when Escape is pressed while streaming", () => {
    const handleStop = vi.fn();
    render(<ChatInput onSend={vi.fn()} onStop={handleStop} isStreaming={true} />);
    const textarea = screen.getByRole("textbox");

    fireEvent.keyDown(textarea, { key: "Escape" });
    expect(handleStop).toHaveBeenCalled();
  });

  it("keeps a drafted follow-up when Enter is pressed during an answer", () => {
    const onSend = vi.fn();
    const onStop = vi.fn();
    render(<ChatInput onSend={onSend} onStop={onStop} isStreaming={true} />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "A drafted follow-up" } });
    fireEvent.keyDown(textarea, { key: "Enter" });
    expect(onSend).not.toHaveBeenCalled();
    expect(onStop).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("A drafted follow-up");

    const stop = screen.getByRole("button", { name: "Stop generation" });
    const click = createEvent.click(stop);
    fireEvent(stop, click);
    expect(click.defaultPrevented).toBe(true);
    expect(onStop).toHaveBeenCalledOnce();
    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("A drafted follow-up");
  });

  it("leaves Enter for IME composition and keeps Shift+Enter for a new line", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} onStop={vi.fn()} isStreaming={false} />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "こんにちは" } });
    fireEvent.keyDown(textarea, { key: "Enter", isComposing: true, keyCode: 229 });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(onSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("こんにちは");
    fireEvent.keyDown(textarea, { key: "Enter" });
    expect(onSend).toHaveBeenCalledWith("こんにちは");
  });

  it("leaves focus inside an open modal when Ctrl+K is pressed", () => {
    render(<>
      <ChatInput onSend={vi.fn()} onStop={vi.fn()} isStreaming={false} />
      <div role="dialog" aria-modal="true"><button type="button">Dialog control</button></div>
    </>);
    const button = screen.getByRole("button", { name: "Dialog control" });
    button.focus();
    fireEvent.keyDown(button, { key: "k", ctrlKey: true });
    expect(button).toHaveFocus();
  });
});
