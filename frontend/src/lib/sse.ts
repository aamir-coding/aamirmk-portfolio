import { getApiBaseUrl } from "./api";
import type { ProjectCardData, SourceCitation } from "./types";
import {
  SourcesEventPayloadSchema,
  CardEventPayloadSchema,
  TokenEventPayloadSchema,
  DoneEventPayloadSchema,
  ErrorEventPayloadSchema,
} from "./contracts";

export interface StreamChatCallbacks {
  onToken: (token: string) => void;
  onDone: (data: {
    conversation_id: string;
    sources?: SourceCitation[];
    cards?: ProjectCardData[];
  }) => void;
  onError: (error: string) => void;
  onSources?: (sources: SourceCitation[]) => void;
  onCard?: (card: ProjectCardData) => void;
}

export interface StreamChatOptions {
  message: string;
  conversationId?: string;
  signal?: AbortSignal;
  callbacks: StreamChatCallbacks;
  baseUrl?: string;
}

export interface ParsedEvent {
  event: string;
  data: string;
}

/**
 * Parses raw SSE text containing full or partial events separated by \n\n.
 * Returns the parsed events and any leftover trailing buffer.
 */
export function parseSSEBuffer(buffer: string): {
  events: ParsedEvent[];
  remaining: string;
} {
  const parts = buffer.split("\n\n");
  const remaining = parts.pop() ?? "";
  const events: ParsedEvent[] = [];

  for (const part of parts) {
    if (!part.trim()) continue;
    let event = "message";
    const dataLines: string[] = [];

    const lines = part.split("\n");
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("event:")) {
        event = trimmed.replace("event:", "").trim();
      } else if (trimmed.startsWith("data:")) {
        dataLines.push(trimmed.replace("data:", "").trim());
      }
    }

    if (dataLines.length > 0) {
      events.push({ event, data: dataLines.join("\n") });
    }
  }

  return { events, remaining };
}

/**
 * Streams conversation completion from FastAPI backend using Server-Sent Events (SSE) over POST.
 * Zero external client dependencies (pure fetch + ReadableStream).
 */
export async function streamChat({
  message,
  conversationId,
  signal,
  callbacks,
  baseUrl,
}: StreamChatOptions): Promise<void> {
  const base = baseUrl ?? getApiBaseUrl();
  const url = `${base}/api/chat/stream`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
      signal,
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorJson = (await response.json()) as {
          error?: { message?: string };
          detail?: string | unknown;
        };
        if (errorJson.error?.message) {
          errorMessage = errorJson.error.message;
        } else if (errorJson.detail) {
          errorMessage =
            typeof errorJson.detail === "string"
              ? errorJson.detail
              : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fall back to HTTP status message if not JSON
      }
      callbacks.onError(errorMessage);
      return;
    }

    if (!response.body) {
      callbacks.onError("ReadableStream not supported by environment");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    const dispatchEvent = (event: string, data: string) => {
      try {
        const parsed = JSON.parse(data);
        if (event === "sources") {
          const res = SourcesEventPayloadSchema.safeParse(parsed);
          if (res.success) {
            callbacks.onSources?.(res.data.sources);
          }
        } else if (event === "card") {
          const res = CardEventPayloadSchema.safeParse(parsed);
          if (res.success) {
            callbacks.onCard?.(res.data.card);
          }
        } else if (event === "token") {
          const res = TokenEventPayloadSchema.safeParse(parsed);
          if (res.success) {
            callbacks.onToken(res.data.token);
          }
        } else if (event === "done") {
          const res = DoneEventPayloadSchema.safeParse(parsed);
          if (res.success) {
            callbacks.onDone({
              conversation_id: res.data.conversation_id,
              sources: res.data.sources,
              cards: res.data.cards,
            });
          }
        } else if (event === "error") {
          const res = ErrorEventPayloadSchema.safeParse(parsed);
          callbacks.onError(
            res.success ? res.data.detail : "An error occurred during streaming"
          );
        }
      } catch {
        // Ignore JSON parse errors for non-JSON comments or keep-alives
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const { events, remaining } = parseSSEBuffer(buffer);
      buffer = remaining;

      for (const { event, data } of events) {
        dispatchEvent(event, data);
      }
    }

    if (buffer.trim()) {
      const { events } = parseSSEBuffer(buffer + "\n\n");
      for (const { event, data } of events) {
        dispatchEvent(event, data);
      }
    }
  } catch (err: unknown) {
    if (signal?.aborted) {
      return;
    }
    const errMsg = err instanceof Error ? err.message : "Network error";
    callbacks.onError(errMsg);
  }
}
