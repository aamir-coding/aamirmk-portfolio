import { useState, useRef, useCallback, useEffect } from "react";
import { streamChat } from "../lib/sse";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: "pending" | "streaming" | "done" | "error";
  timestamp: string;
}

export interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  conversationId: string | null;
  error: string | null;
  sendMessage: (text: string) => Promise<void>;
  stopStreaming: () => void;
  clearError: () => void;
  resetChat: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
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
  }, []);

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
    setMessages((prev) =>
      prev.map((msg) =>
        msg.status === "streaming" ? { ...msg, status: "done" } : msg
      )
    );
  }, []);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      setError(null);
      const userMessageId = `user-${Date.now()}`;
      const assistantMessageId = `assistant-${Date.now()}`;
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
          onToken: (token) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: msg.content + token }
                  : msg
              )
            );
          },
          onDone: (data) => {
            if (data.conversation_id) {
              setConversationId(data.conversation_id);
            }
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, status: "done" }
                  : msg
              )
            );
            setIsStreaming(false);
            abortControllerRef.current = null;
          },
          onError: (errMsg) => {
            setError(errMsg);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? {
                      ...msg,
                      status: "error",
                      content:
                        msg.content ||
                        "An error occurred while generating the response.",
                    }
                  : msg
              )
            );
            setIsStreaming(false);
            abortControllerRef.current = null;
          },
        },
      });
    },
    [conversationId, isStreaming]
  );

  return {
    messages,
    isStreaming,
    conversationId,
    error,
    sendMessage,
    stopStreaming,
    clearError,
    resetChat,
  };
}
