import React from "react";
import type { ChatMessage } from "../../lib/types";
import { SourceChips } from "./SourceChips";

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
        <span className="chat-message-badge">
          {isUser ? "INQUIRY" : "DISPATCH"}
        </span>
        <span className="chat-message-author">
          {isUser ? "Recruiter" : "Aamir.AI"}
        </span>
        <time className="chat-message-time">{message.timestamp}</time>
      </header>
      <div className="chat-message-body">
        {message.content && (
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
        )}
        {message.status === "streaming" && !message.content && (
          <p className="chat-message-text">
            <span
              className="streaming-cursor"
              aria-hidden="true"
              data-testid="streaming-cursor"
            >
              ▍
            </span>
          </p>
        )}
        {message.status === "error" && !message.content && (
          <p className="chat-message-error" role="alert">
            Generation interrupted or failed.
          </p>
        )}
        {!isUser && message.sources && message.sources.length > 0 && (
          <SourceChips sources={message.sources} />
        )}
      </div>
    </article>
  );
});
