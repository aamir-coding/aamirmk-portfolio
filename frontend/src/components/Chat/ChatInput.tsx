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
    }
  };

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
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
            ? "Assistant is responding..."
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
    </form>
  );
}
