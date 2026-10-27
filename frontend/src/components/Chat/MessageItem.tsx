import React from "react";
import type { ChatMessage } from "../../hooks/useChat";

export interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem = React.memo(function MessageItem({
  message,
}: MessageItemProps) {
  const isUser = message.role === "user";

  return (
    <article
      className={`chat-message ${
        isUser ? "chat-message-user" : "chat-message-assistant"
      }`}
      aria-label={`${isUser ? "User" : "Assistant"} message`}
    >
      <header className="chat-message-header">
        <span className="chat-message-author">
          {isUser ? "You" : "Assistant"}
        </span>
        <time className="chat-message-time">{message.timestamp}</time>
      </header>
      <div className="chat-message-body">
        <p className="chat-message-text">
          {message.content}
          {message.status === "streaming" && (
            <span
              className="streaming-cursor"
              aria-hidden="true"
              data-testid="streaming-cursor"
            >
              ▍
            </span>
          )}
        </p>
        {message.status === "error" && (
          <p className="chat-message-error" role="alert">
            Generation interrupted or failed.
          </p>
        )}
      </div>
    </article>
  );
});
