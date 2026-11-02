import { useState, useRef, useCallback, useEffect } from "react";
import { streamChat } from "../lib/sse";
import type {
  ChatMessage,
  ProjectCardData,
  SourceCitation,
  InstantAnswer,
} from "../lib/types";

export type { ChatMessage };

export const CHAT_SESSION_STORAGE_KEY = "amk_portfolio_chat_session";

export interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  conversationId: string | null;
  error: string | null;
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

  const abortControllerRef = useRef<AbortController | null>(null);

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
        msg.status === "streaming" ? { ...msg, status: "done" as const } : msg
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

      const controller = new AbortController();
      abortControllerRef.current = controller;

      await streamChat({
        message: trimmed,
        conversationId: conversationId ?? undefined,
        signal: controller.signal,
        callbacks: {
          onSources: (sources: SourceCitation[]) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId ? { ...msg, sources } : msg
              )
            );
          },
          onCard: (card: ProjectCardData) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, cards: [...(msg.cards || []), card] }
                  : msg
              )
            );
          },
          onToken: (token: string) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + token }
                  : msg
              )
            );
          },
          onDone: (data) => {
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
          onError: (errMsg: string) => {
            setError(errMsg);
            setMessages((prev) => {
              const updated = prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      status: "error" as const,
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
