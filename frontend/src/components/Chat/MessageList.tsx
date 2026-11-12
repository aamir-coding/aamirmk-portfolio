import { useRef, useEffect } from "react";
import type { ChatMessage } from "../../hooks/useChat";
import type { CompanyContext } from "../../lib/api";
import { MessageItem } from "./MessageItem";
import { CoverState } from "../Cover/CoverState";

export interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  isCoverState?: boolean;
  company?: CompanyContext | null;
  onSelectPrompt: (prompt: string) => void;
  onOpenFitModal?: () => void;
}

export function MessageList({
  messages,
  isStreaming,
  isCoverState = false,
  company,
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
          company={company}
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
      {messages.map((message, index) => {
        const transcript = message.handoffId
          ? messages.slice(0, index + 1)
            .filter(item => item.status === "done" && item.delivery !== "cancelled" && item.content.trim())
            .slice(-10)
            .map(({ role, content }) => ({ role, content }))
          : undefined;
        return <MessageItem key={message.id} message={message} handoffTranscript={transcript} />;
      })}
      <div ref={bottomRef} aria-hidden="true" />
    </div>
  );
}
