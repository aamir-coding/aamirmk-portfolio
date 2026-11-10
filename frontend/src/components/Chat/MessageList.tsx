import { useRef, useEffect } from "react";
import type { ChatMessage } from "../../hooks/useChat";
import { MessageItem } from "./MessageItem";
import { CoverState } from "../Cover/CoverState";

export interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  isCoverState?: boolean;
  onSelectPrompt: (prompt: string) => void;
  onOpenFitModal?: () => void;
}

export function MessageList({
  messages,
  isStreaming,
  isCoverState = false,
  onSelectPrompt,
  onOpenFitModal,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [messages]);

  if (isCoverState || messages.length === 0) {
    return (
      <div className="chat-empty-state" role="group" aria-label="Welcome and suggestions">
        <CoverState
          onSelectPrompt={onSelectPrompt}
          onOpenFitModal={onOpenFitModal}
          disabled={isStreaming}
        />
      </div>
    );
  }

  return (
    <div
      className="chat-message-list"
      role="log"
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
