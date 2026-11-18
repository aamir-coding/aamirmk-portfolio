import { useRef, useEffect } from "react";
import type { ChatMessage } from "../../hooks/useChat";
import { MessageItem } from "./MessageItem";

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  const logRef = useRef<HTMLDivElement>(null);
  const followsLatest = useRef(messages.length > 2);
  const previousCount = useRef(messages.length);

  useEffect(() => {
    const log = logRef.current;
    if (messages.length > previousCount.current) followsLatest.current = true;
    previousCount.current = messages.length;
    if (log && followsLatest.current) log.scrollTop = log.scrollHeight;
  }, [messages]);

  return (
    <div
      ref={logRef}
      className="chat-message-list"
      role="log"
      aria-label="Conversation history"
      aria-live="polite"
      tabIndex={0}
      onScroll={({ currentTarget: log }) => {
        followsLatest.current = log.scrollHeight - log.scrollTop - log.clientHeight < 48;
      }}
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
    </div>
  );
}
