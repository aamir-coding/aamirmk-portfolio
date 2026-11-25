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
    if (isStreaming) return;
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
                // The same control becomes a submit button when the stream stops.
                event.preventDefault();
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
              className="btn send-control"
              onClick={(event) => keepComposerFocus(event.detail)}
              disabled={disabled || !input.trim()}
              aria-label="Ask a question"
            >
              <svg aria-hidden="true" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 19V5m-6.5 6.5L12 5l6.5 6.5" />
              </svg>
            </button>
          )}
        </div>
      </div>
      <div className="chat-input-helper">
        <span className="chat-input-keys">
          <span>Enter to send</span>
          <span>Shift+Enter for a new line</span>
          <kbd className="kbd-shortcut" title="Focus composer (Ctrl+K or ⌘K)">
            Ctrl+K
          </kbd>
        </span>
        {isStreaming && (
          <span className="helper-active">Esc to stop</span>
        )}
      </div>
    </form>
  );
}
