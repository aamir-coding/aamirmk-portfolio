import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import type { ChatMessage } from "../../hooks/useChat";
import { MessageItem } from "./MessageItem";

import type { ProjectCardData } from "../../lib/types";
import type { ShowcaseId } from "../Cover/projects";

interface MessageListProps {
  onInspectProject?: (id: ShowcaseId, card?: ProjectCardData) => void;
  messages: ChatMessage[];
  isStreaming: boolean;
  onOverview: () => void;
  onClear: () => void;
}

function isNearLatest(log: HTMLDivElement) {
  return log.scrollHeight - log.scrollTop - log.clientHeight < 48;
}

export function MessageList({ messages, isStreaming, onOverview, onClear, onInspectProject }: MessageListProps) {
  const logRef = useRef<HTMLDivElement>(null);
  const jumpRef = useRef<HTMLButtonElement>(null);
  const followsLatest = useRef(messages.length > 2);
  const previousCount = useRef(messages.length);
  const previousLatest = useRef(messages.at(-1));
  const [showJump, setShowJump] = useState(false);

  const syncScrollPosition = useCallback((log: HTMLDivElement) => {
    followsLatest.current = isNearLatest(log);
    if (followsLatest.current && jumpRef.current === document.activeElement) {
      log.focus({ preventScroll: true });
    }
    setShowJump(!followsLatest.current);
  }, []);

  useEffect(() => {
    const log = logRef.current;
    if (!log) return;
    // A disclosure changes the transcript height without a scroll event.
    const onToggle = () => syncScrollPosition(log);
    log.addEventListener("toggle", onToggle, true);
    return () => log.removeEventListener("toggle", onToggle, true);
  }, [syncScrollPosition]);

  useLayoutEffect(() => {
    const log = logRef.current;
    if (!log) return;
    const latest = messages.at(-1);
    const previous = previousLatest.current;
    // Evidence can expand the last turn at completion. Keep the answer in view.
    const settledWithText = previous?.status === "streaming"
      && latest?.id === previous.id
      && latest.status !== "streaming"
      && Boolean(latest.content.trim());
    previousLatest.current = latest;
    if (messages.length > previousCount.current) followsLatest.current = true;
    previousCount.current = messages.length;
    if (followsLatest.current && !settledWithText) log.scrollTop = log.scrollHeight;
    const atLatest = isNearLatest(log);
    if (settledWithText) followsLatest.current = atLatest;
    if (atLatest && jumpRef.current === document.activeElement) log.focus({ preventScroll: true });
    setShowJump(!atLatest);
  }, [messages]);

  const jumpToLatest = () => {
    const log = logRef.current;
    if (!log) return;
    followsLatest.current = true;
    log.scrollTop = log.scrollHeight;
    log.focus({ preventScroll: true });
    setShowJump(false);
  };

  return (
    <>
      <div className="portfolio-transcript-actions" aria-label="Conversation controls" role="group">
        <button type="button" aria-label="Portfolio overview" onClick={onOverview}>Overview</button>
        <button type="button" onClick={onClear} disabled={isStreaming}>Clear chat</button>
        {showJump && (
          <button ref={jumpRef} type="button" aria-controls="chat-history" onClick={jumpToLatest}>
            Jump to latest
          </button>
        )}
      </div>
      <div
        ref={logRef}
        id="chat-history"
        className="chat-message-list"
        role="region"
        aria-label="Conversation history"
        tabIndex={0}
        onScroll={({ currentTarget: log }) => syncScrollPosition(log)}
      >
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
    </>
  );
}
