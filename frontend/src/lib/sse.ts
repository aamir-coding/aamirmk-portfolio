import { getApiBaseUrl } from "./api";

export interface StreamChatCallbacks {
  onToken: (token: string) => void;
  onDone: (data: { conversation_id: string }) => void;
  onError: (error: string) => void;
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

export async function streamChat({
  message,
  conversationId,
  signal,
  callbacks,
  baseUrl = getApiBaseUrl(),
}: StreamChatOptions): Promise<void> {
  const endpoint = `${baseUrl}/api/chat/stream`;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
      signal,
    });

    if (!response.ok) {
      let errorMessage = `Request failed with HTTP ${response.status}`;
      try {
        const errorJson = (await response.json()) as {
          error?: { message?: string };
          detail?: string | unknown;
        };
        if (errorJson?.error?.message) {
          errorMessage = errorJson.error.message;
        } else if (errorJson?.detail) {
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
      callbacks.onError("No response body received from server");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const { events, remaining } = parseSSEBuffer(buffer);
      buffer = remaining;

      for (const { event, data } of events) {
        try {
          const parsed = JSON.parse(data) as Record<string, unknown>;
          if (event === "token" && typeof parsed.token === "string") {
            callbacks.onToken(parsed.token);
          } else if (event === "done") {
            callbacks.onDone({
              conversation_id:
                typeof parsed.conversation_id === "string"
                  ? parsed.conversation_id
                  : "",
            });
          } else if (event === "error") {
            const detail =
              typeof parsed.detail === "string"
                ? parsed.detail
                : "An error occurred during streaming";
            callbacks.onError(detail);
          }
        } catch {
          // Ignore JSON parse errors for non-JSON comments or keep-alives
        }
      }
    }

    if (buffer.trim()) {
      const { events } = parseSSEBuffer(buffer + "\n\n");
      for (const { event, data } of events) {
        try {
          const parsed = JSON.parse(data) as Record<string, unknown>;
          if (event === "token" && typeof parsed.token === "string") {
            callbacks.onToken(parsed.token);
          } else if (event === "done") {
            callbacks.onDone({
              conversation_id:
                typeof parsed.conversation_id === "string"
                  ? parsed.conversation_id
                  : "",
            });
          } else if (event === "error") {
            const detail =
              typeof parsed.detail === "string"
                ? parsed.detail
                : "An error occurred during streaming";
            callbacks.onError(detail);
          }
        } catch {
          // ignore
        }
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
