import { useLayoutEffect, useRef } from "react";
import type { ChatMessage, ProjectCardData } from "../../lib/types";
import type { ShowcaseId } from "../Cover/projects";
import { MessageItem } from "./MessageItem";

interface MessageListProps {
  messages: ChatMessage[];
  onInspectProject?: (id: ShowcaseId, card?: ProjectCardData) => void;
}

export function MessageList({ messages, onInspectProject }: MessageListProps) {
  const logRef = useRef<HTMLDivElement>(null);
  const latestId = messages.at(-1)?.id;

  useLayoutEffect(() => {
    const log = logRef.current;
    const answer = log?.lastElementChild;
    if (!log || !answer) return;
    const question = answer.previousElementSibling;
    // Keep a short question for context. A pasted brief can fill several screens.
    const start = question && question.getBoundingClientRect().height < log.clientHeight * .4
      ? question : answer;
    const contextHeight = answer.getBoundingClientRect().top - start.getBoundingClientRect().top;
    log.style.setProperty("--turn-context", `${contextHeight}px`);
    log.scrollTop += start.getBoundingClientRect().top - log.getBoundingClientRect().top;
  }, [latestId]);

  return (
    <div ref={logRef} id="chat-history" className="chat-message-list"
      role="region" aria-label="Conversation history" tabIndex={0}>
      {messages.map((message, index) => {
        const transcript = message.handoffId
          ? messages.slice(0, index + 1)
            .filter(item => item.status === "done" && item.delivery !== "cancelled" && item.content.trim())
            .slice(-10)
            .map(({ role, content }) => ({ role, content }))
          : undefined;
        return <MessageItem key={message.id} message={message} onInspectProject={onInspectProject} handoffTranscript={transcript} />;
      })}
    </div>
  );
}
