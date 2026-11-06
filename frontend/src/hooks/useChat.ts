import type { RequestTelemetry } from "../lib/contracts";
import { useState, useRef, useCallback, useEffect } from "react";
import { streamChat } from "../lib/sse";
import type {
  ChatMessage,
  ProjectCardData,
  SourceCitation,
  InstantAnswer,
} from "../lib/types";

export type { ChatMessage };

export const CHAT_SESSION_STORAGE_KEY = "amk_portfolio_chat_session_v2";

export interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  conversationId: string | null;
  error: string | null;
  isResting?: boolean;
  sendMessage: (text: string) => Promise<void>;
  sendInstantAnswer: (question: string, answer: InstantAnswer) => void;
  stopStreaming: () => void;
  clearError: () => void;
  resetChat: () => void;
}

function loadPersistedChat(): {
  messages: ChatMessage[];
  conversationId: string | null;
} {
  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      window.sessionStorage.removeItem("amk_portfolio_chat_session"); // purge stale v1 transcript
      const raw = window.sessionStorage.getItem(CHAT_SESSION_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed?.messages)) {
          return {
            messages: parsed.messages,
            conversationId: parsed.conversationId || null,
          };
        }
      }
    }
  } catch {
    // sessionStorage disabled or unavailable
  }
  return { messages: [], conversationId: null };
}

function savePersistedChat(
  messages: ChatMessage[],
  conversationId: string | null
): void {
  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      window.sessionStorage.setItem(
        CHAT_SESSION_STORAGE_KEY,
        JSON.stringify({ messages, conversationId })
      );
    }
  } catch {
    // sessionStorage quota exceeded or restricted
  }
}

export function useChat(): UseChatReturn {
  const initial = loadPersistedChat();
  const [messages, setMessages] = useState<ChatMessage[]>(initial.messages);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(
    initial.conversationId
  );
  const [error, setError] = useState<string | null>(null);
  const [isResting, setIsResting] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  // Clean up any in-flight stream on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const resetChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
    setIsStreaming(false);
    setConversationId(null);
    setError(null);
    try {
      if (typeof window !== "undefined" && window.sessionStorage) {
        window.sessionStorage.removeItem(CHAT_SESSION_STORAGE_KEY);
      }
    } catch {
      // storage unavailable
    }
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setMessages((prev) => {
      const updated = prev.map((msg) =>
        msg.status === "streaming" ? { ...msg, status: "done" as const, delivery: "cancelled" as const } : msg
      );
      savePersistedChat(updated, conversationId);
      return updated;
    });
  }, [conversationId]);

  const sendInstantAnswer = useCallback(
    (question: string, answer: InstantAnswer) => {
      setError(null);
      const userMessageId = `user-${Date.now()}`;
      const assistantMessageId = `assistant-${Date.now() + 1}`;
      const timestamp = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      const userMessage: ChatMessage = {
        id: userMessageId,
        role: "user",
        content: question.trim(),
        status: "done",
        timestamp,
      };

      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: answer.reply,
        delivery: "instant",
        status: "done",
        timestamp,
        sources: answer.sources || [],
        cards: [],
      };

      setMessages((prev) => {
        const next = [...prev, userMessage, assistantMessage];
        savePersistedChat(next, conversationId);
        return next;
      });
    },
    [conversationId]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      setError(null);
      const userMessageId = `user-${Date.now()}`;
      const assistantMessageId = `assistant-${Date.now() + 1}`;
      const timestamp = new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });

      const userMessage: ChatMessage = {
        id: userMessageId,
        role: "user",
        content: trimmed,
        status: "done",
        timestamp,
      };

      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        status: "streaming",
        timestamp,
        sources: [],
        cards: [],
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      // Extract recent completed messages as conversational history for multi-turn context
      const historyPayload = messagesRef.current
        .filter((m) => m.status === "done" && m.content.trim().length > 0)
        .slice(-6)
        .map((m) => ({ role: m.role, content: m.content }));

      const controller = new AbortController();
      abortControllerRef.current = controller;

      await streamChat({
        message: trimmed,
        conversationId: conversationId ?? undefined,
        history: historyPayload,
        signal: controller.signal,
        callbacks: {
          onState: () => { if (!controller.signal.aborted) setIsResting(true); },
          onSources: (sources: SourceCitation[]) => {
            if (controller.signal.aborted) return;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, sources } : msg
              )
            );
          },
          onCard: (card: ProjectCardData) => {
            if (controller.signal.aborted) return;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, cards: [...(msg.cards || []), card] }
                  : msg
              )
            );
          },
          onToken: (token: string) => {
            if (controller.signal.aborted) return;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + token }
                  : msg
              )
            );
          },
          onDone: (data) => {
            if (controller.signal.aborted) return;
            setIsResting(false);
            let activeConvId = conversationId;
            if (data.conversation_id) {
              setConversationId(data.conversation_id);
              activeConvId = data.conversation_id;
            }
            setMessages((prev) => {
              const updated = prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      status: "done" as const,
                      telemetry: data.telemetry,
                      browserTiming: data.browserTiming,
                      sources:
                        msg.sources && msg.sources.length > 0
                          ? msg.sources
                          : data.sources || [],
                      cards:
                        msg.cards && msg.cards.length > 0
                          ? msg.cards
                          : data.cards || [],
                    }
                  : msg
              );
              savePersistedChat(updated, activeConvId);
              return updated;
            });
            setIsStreaming(false);
            abortControllerRef.current = null;
          },
          onError: (errMsg: string, telemetry?: RequestTelemetry) => {
            if (controller.signal.aborted) return;
            setError(errMsg);
            setMessages((prev) => {
              const updated = prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      status: "error" as const,
                      telemetry,
                      content:
                        msg.content ||
                        errMsg ||
                        "Generation failed. Please try again.",
                    }
                  : msg
              );
              savePersistedChat(updated, conversationId);
              return updated;
            });
            setIsStreaming(false);
            abortControllerRef.current = null;
          },
        },
      });
    },
    [isStreaming, conversationId]
  );

  return {
    isResting,
    messages,
    isStreaming,
    conversationId,
    error,
    sendMessage,
    sendInstantAnswer,
    stopStreaming,
    clearError,
    resetChat,
  };
}
