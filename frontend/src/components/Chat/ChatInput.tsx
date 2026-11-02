import {
  useState,
  useRef,
  useEffect,
  type FormEvent,
  type KeyboardEvent,
} from "react";

export interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onStop,
  isStreaming,
  disabled = false,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isStreaming && !disabled) {
      textareaRef.current?.focus();
    }
  }, [isStreaming, disabled]);

  // Global Ctrl+K / Cmd+K shortcut to focus input
  useEffect(() => {
    const handleGlobalKeyDown = (e: globalThis.KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        textareaRef.current?.focus();
        textareaRef.current?.select();
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => {
      window.removeEventListener("keydown", handleGlobalKeyDown);
    };
  }, []);

  const handleSubmit = (e?: FormEvent) => {
    if (e) e.preventDefault();
    if (isStreaming) {
      onStop();
      return;
    }
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === "Escape" && isStreaming) {
      e.preventDefault();
      onStop();
    }
  };

  return (
    <form className="chat-input-form-wrapper" onSubmit={handleSubmit}>
      <div className="chat-input-row">
        <label htmlFor="chat-user-input" className="sr-only">
          Ask a question about Aamir's background
        </label>
        <textarea
          id="chat-user-input"
          ref={textareaRef}
          className="chat-textarea"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            isStreaming
              ? "Assistant dispatch in progress..."
              : "Ask about Aamir's experience, stack, or projects (Enter to send, Shift+Enter for newline)..."
          }
          rows={2}
          disabled={disabled}
          aria-disabled={disabled}
        />
        <div className="chat-input-actions">
          {isStreaming ? (
            <button
              type="button"
              className="btn btn-stop"
              onClick={onStop}
              aria-label="Stop generation"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              disabled={disabled || !input.trim()}
              aria-label="Send message"
            >
              Send
            </button>
          )}
        </div>
      </div>
      <div className="chat-input-helper">
        <span>
          Enter to dispatch • Shift+Enter for newline •{" "}
          <kbd className="kbd-shortcut" title="Focus composer (Ctrl+K or ⌘K)">
            Ctrl+K
          </kbd>
        </span>
        {isStreaming && (
          <span className="helper-active">Streaming active • Esc to stop</span>
        )}
      </div>
    </form>
  );
}
