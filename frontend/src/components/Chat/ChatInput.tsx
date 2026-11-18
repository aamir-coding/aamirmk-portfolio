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
    const handleGlobalKeyDown = (e: globalThis.KeyboardEvent) => {
      const textarea = textareaRef.current;
      if (!textarea || textarea.disabled || e.defaultPrevented || e.isComposing) return;
      if (!(e.ctrlKey || e.metaKey) || e.altKey || e.shiftKey || e.key.toLowerCase() !== "k") return;
      if (document.querySelector('[aria-modal="true"], dialog[open]')) return;
      e.preventDefault();
      textarea.focus();
      textarea.select();
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

  const keepComposerFocus = (clickCount: number) => {
    if (clickCount === 0) textareaRef.current?.focus({ preventScroll: true });
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.nativeEvent.isComposing || e.keyCode === 229) return;
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
              ? "Draft your next question"
              : "Ask about Aamir’s work"
          }
          rows={1}
          disabled={disabled}
          aria-disabled={disabled}
        />
        <div className="chat-input-actions">
          {isStreaming ? (
            <button
              type="button"
              className="btn btn-stop"
              onClick={(event) => {
                keepComposerFocus(event.detail);
                onStop();
              }}
              aria-label="Stop generation"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              onClick={(event) => keepComposerFocus(event.detail)}
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
          Enter to send · Shift+Enter for a new line ·{" "}
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
