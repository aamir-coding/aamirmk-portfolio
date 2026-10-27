import { useRef, useEffect } from "react";
import type { ChatMessage } from "../../hooks/useChat";
import { MessageItem } from "./MessageItem";
import { StarterChips } from "./StarterChips";

export interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSelectPrompt: (prompt: string) => void;
}

export function MessageList({
  messages,
  isStreaming,
  onSelectPrompt,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="chat-empty-state" aria-label="Welcome and suggestions">
        <section className="chat-intro">
          <h2 className="chat-intro-title">Aamir Mohammed Khan</h2>
          <p className="chat-intro-subtitle">
            AI Systems & Full-Stack Engineer
          </p>
          <p className="chat-intro-body">
            I’m an AI digital assistant trained exclusively on Aamir’s verified
            résumé, technical projects, and engineering experience. Ask me about
            his stack, architecture decisions, or measurable impact.
          </p>
        </section>
        <StarterChips onSelect={onSelectPrompt} disabled={isStreaming} />
      </div>
    );
  }

  return (
    <div
      className="chat-message-list"
      aria-label="Conversation history"
      aria-live="polite"
    >
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}
