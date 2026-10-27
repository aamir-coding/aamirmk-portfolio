# Phase 3 Study Guide: Streaming (SSE over POST), React Chat MVP & Cold-Start UX

> **Purpose**: This guide provides the complete theoretical foundation, architectural rationale, line-by-line code connections, and placement interview preparation for everything built in Phase 3 (`phase-3-streaming-chat`). Use this document for technical revision and AI/full-stack engineering interviews.

---

## 1. Core Engineering Concepts & "Why"

### 1.1 Streaming Architectures: Server-Sent Events (SSE) vs. WebSockets vs. Polling
When serving generative AI responses, Time to First Token (TTFT) is the defining user experience metric. Waiting for a full 500-token completion might take 3–5 seconds, whereas streaming tokens allows the user to begin reading within 500ms.

| Attribute | HTTP Polling | WebSockets | Server-Sent Events (SSE) |
| :--- | :--- | :--- | :--- |
| **Protocol** | Periodic HTTP GET/POST | Full-duplex TCP (`ws://` / `wss://`) | Persistent HTTP (`text/event-stream`) |
| **Directionality** | Unidirectional (Client pulls) | Bidirectional (Full duplex) | Unidirectional (Server pushes) |
| **Connection Overhead** | High (handshake per poll) | Upgraded connection, persistent | Standard HTTP request/response |
| **Proxy / CDN Traversal** | Trivial (standard HTTP) | Complex (often blocked or terminated by enterprise firewalls/proxies) | Native HTTP (traverses standard HTTP proxies cleanly) |
| **HTTP/2 Multiplexing** | Yes | No (requires separate TCP connection) | Yes (shares single TCP connection with other HTTP/2 streams) |
| **Ideal Use Case** | Infrequent status checks | Real-time gaming, collaborative canvas, bidirectional audio | **LLM Token Streaming, notification feeds** |

**Why SSE is the superior choice for LLM completions:**
1. **Unidirectional Match**: Generative AI chat is inherently unidirectional once the prompt is submitted: the client sends one message, and the server pushes dozens of token chunks until complete.
2. **Infrastructure Simplicity**: WebSockets require stateful connection negotiation, ping/pong heartbeats, and dedicated connection managers in ASGI. SSE works over standard HTTP/1.1 or HTTP/2 responses.
3. **Free-Tier Resilience**: Platforms like Render and Vercel handle standard HTTP streaming seamlessly without requiring persistent WebSocket proxy timeouts or dedicated WebSocket servers.

---

### 1.2 SSE over HTTP POST vs. The Standard Browser `EventSource`
The browser's native `EventSource` API (`new EventSource(url)`) has a fatal architectural limitation: **it only supports HTTP GET requests**.

- **Why GET Fails for Conversational AI**:
  - LLM prompts can easily exceed URL length limits (often 2 KB to 8 KB across browsers and reverse proxies).
  - In later phases, requests include conversation history, client session metadata, and candidate job descriptions (JDs) for fit evaluation.
  - Passing prompts in query strings leaks user queries into HTTP server access logs and browser histories.
- **The Solution: Hand-Built SSE over HTTP POST**:
  By using the Fetch API with the browser Streams API (`response.body.getReader()`), we can send a standard JSON `POST` body with strict Pydantic validation (`ChatRequest`), while consuming the response as an asynchronous stream of UTF-8 byte chunks.

---

### 1.3 TCP Packet Fragmentation & The Split-Chunk Problem
A fundamental trap in streaming clients is assuming that each `reader.read()` corresponds to exactly one SSE event block (`data: {"token": "..."}\n\n`).

Under the hood:
1. TCP is a **stream-oriented protocol**, not a message-oriented protocol. It does not know where an SSE event begins or ends.
2. MTU (Maximum Transmission Unit) limits and network jitter cause arbitrary fragmentation:
   - **Chunk 1**: `event: token\ndata: {"to`
   - **Chunk 2**: `ken": "FastAPI"}\n\nevent: to`
   - **Chunk 3**: `ken\ndata: {"token": " and"}\n\n`
3. If a client attempts `JSON.parse(chunk)` directly on each read, it will throw `SyntaxError: Unexpected end of JSON input` whenever an event crosses a packet boundary.

**Our Accumulator Solution (`frontend/src/lib/sse.ts`)**:
```
Incoming Byte Stream ──▶ TextDecoder ──▶ Buffer Accumulator
                                                │
                                       Split by "\n\n"
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
     Complete Event Blocks (0..N)                                     Incomplete Tail
      - Parse lines ("event:", "data:")                               (Preserved in buffer
      - JSON.parse data                                                for next reader chunk)
      - Dispatch to callbacks
```

---

### 1.4 Render Free Tier Cold Starts: The 25-Second Reality
Render's free web service tier spins down instances to 0 instances after **15 minutes of inactivity**.

- **Phase 0 Benchmarks**:
  - Run 1: 23.15s
  - Run 2 (Peak): 32.93s
  - Run 3: 22.71s
  - Average: ~25s.
- **The UX Problem**: If a recruiter visits the site and types a message while the instance is sleeping, a silent 25-second wait makes the app feel completely frozen or broken.
- **The Architectural Mitigation**:
  1. On initial mount, `App.tsx` immediately fires `fetchHealth()`.
  2. If the health check has not resolved after **2.5 seconds**, the UI transitions the status pill to `"Waking Up (Render ~25s)"` and displays an informative banner explaining that the server is booting from idle.
  3. When the instance wakes up and answers, the status pill turns solid green (`"Ready"`), resetting expectations and building recruiter trust.

---

## 2. Line-by-Line Code Walkthrough & Architectural Seams

### 2.1 Backend Adapter Seam (`backend/app/llm.py`)

#### Protocol Extension
```python
class LLMClient(Protocol):
    async def complete(self, messages: list[Message]) -> AssistantMessage: ...
    async def stream(self, messages: list[Message]) -> AsyncIterator[str]: ...
```
- Following the **Deep Module pattern**, `stream()` hides all Groq SDK internals behind a single minimal signature: it accepts a typed message list and yields raw string tokens.
- Callers (like `/api/chat/stream`) know nothing about Groq authentication, model strings, or SDK streaming delta chunks.

#### Production Groq Adapter (`GroqLLM.stream`)
```python
async def stream(self, messages: list[Message]) -> AsyncIterator[str]:
    try:
        response_stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=0.4,
            max_completion_tokens=1024,
            stream=True,
        )
    except Exception as exc:
        self._map_error(exc)

    try:
        async for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as exc:
        self._map_error(exc)
```
- `stream=True`: Instructs Groq's API to stream completion chunks via HTTP chunked transfer encoding.
- `delta.content`: Extracts the incremental token string.
- Two distinct error zones:
  - Error before stream start (e.g., auth failure, immediate rate limit).
  - Error mid-stream (e.g., upstream network drop during token delivery). Both are mapped to domain exceptions (`LLMRateLimitError`, `LLMAuthError`, `LLMUnavailableError`).

#### In-Memory Test Fake (`FakeLLM.stream`)
```python
async def stream(self, messages: list[Message]) -> AsyncIterator[str]:
    self.last_messages = list(messages)
    if self.error_to_raise is not None:
        raise self.error_to_raise
    if self.stream_chunks is not None:
        for chunk in self.stream_chunks:
            yield chunk
    else:
        words = self.reply.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
```
- Yields tokens word-by-word with preserved spacing.
- Guarantees deterministic, sub-millisecond automated tests with 0 API cost.

---

### 2.2 FastAPI SSE Endpoint (`backend/app/api/chat.py`)

```python
@router.post("/chat/stream", status_code=status.HTTP_200_OK)
async def chat_stream(
    request: ChatRequest,
    llm: LLMClient = Depends(get_llm_client),
) -> StreamingResponse:
    conv_id = request.conversation_id or uuid.uuid4().hex
    messages = [
        Message(role="system", content=SYSTEM_PROMPT),
        Message(role="user", content=request.message),
    ]

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for token in llm.stream(messages):
                payload = json.dumps({"token": token})
                yield f"event: token\ndata: {payload}\n\n"

            done_payload = json.dumps({"conversation_id": conv_id})
            yield f"event: done\ndata: {done_payload}\n\n"
        except LLMRateLimitError as exc:
            err_payload = json.dumps({"detail": "Rate limit reached. Please try again in a few moments."})
            yield f"event: error\ndata: {err_payload}\n\n"
        # ... other error handlers

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers,
    )
```
- **Response Headers**:
  - `Cache-Control: no-cache, no-transform`: Prevents intermediate proxies or CDNs from caching or compressing the stream in ways that introduce buffering.
  - `X-Accel-Buffering: no`: Explicitly instructs reverse proxies like Nginx to disable response buffering and flush packets immediately to the client.
- **Typed Event Frames**:
  - `event: token`: Carries incremental text fragments.
  - `event: done`: Emits final conversation metadata (`conversation_id`).
  - `event: error`: Delivers clean in-band error messages if the generator encounters exceptions after HTTP 200 headers have already been transmitted.

---

### 2.3 Hand-Built Frontend SSE Client (`frontend/src/lib/sse.ts`)

```typescript
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

    for (const line of part.split("\n")) {
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
```
- Implements stateful chunk buffering. Any incomplete block trailing after the final `\n\n` is preserved in `remaining` and prepended to the next chunk.
- Fully tested against split JSON packets, multiline event frames, and abrupt stream aborts.

---

### 2.4 React Re-render Optimization & `React.memo`

In high-throughput token streaming (30–60 tokens/sec), naive React implementations re-render the entire conversation tree (all previous user and assistant messages) on every single token.

- In `frontend/src/components/Chat/MessageItem.tsx`:
  ```typescript
  export const MessageItem = React.memo(function MessageItem({ message }: MessageItemProps) {
    // ...
  });
  ```
- **Why this matters**:
  - `React.memo` performs shallow comparison of props.
  - Only the currently streaming message whose `content` string reference changes triggers a DOM repaint.
  - All previously completed messages remain untouched, preserving 60 FPS scrolling and low CPU usage on mobile devices.

---

## 3. Placement & Architecture Interview Questions

### Q1: Why did you choose Server-Sent Events (SSE) over WebSockets for an LLM assistant?
> **Answer**:
> "WebSockets are designed for bidirectional, full-duplex communication (like multiplayer gaming or live audio feeds). An LLM assistant conversation, however, is fundamentally request-response where the response happens to be streamed: the user submits a single prompt, and the server pushes tokens until completion.
> 
> SSE operates directly over standard HTTP/1.1 or HTTP/2 without requiring protocol upgrades (`101 Switching Protocols`), complex connection state machines, or dedicated WebSocket gateways. In HTTP/2 environments, SSE streams multiplex over existing TCP connections. Furthermore, SSE is firewall- and proxy-friendly, which is critical when deploying on free-tier platforms like Render or Vercel where WebSocket proxy idle timeouts are frequently terminated."

---

### Q2: Browser `EventSource` only supports GET. How did you stream over POST, and how did you prevent TCP packet fragmentation bugs?
> **Answer**:
> "To avoid URL character length restrictions and prevent leaking prompt content into HTTP access logs, we built a zero-dependency SSE client over HTTP POST using `fetch()` and the browser's native `ReadableStreamDefaultReader` with `TextDecoder`.
> 
> Because TCP is stream-oriented and packets can split arbitrary UTF-8 or JSON boundaries, we implemented an event accumulator: incoming decoded chunks are appended to a persistent buffer string, which is split on double-newlines (`\n\n`) representing SSE event boundaries. Completed blocks are parsed into event type and JSON data payloads, while any partial trailing fragment is retained in the buffer and prepended to the subsequent network chunk. This guarantees zero JSON parse errors even under heavy network fragmentation."

---

### Q3: During rapid token streaming (50+ tokens per second), React applications can suffer from severe re-render lag. How did you architect the frontend for performance?
> **Answer**:
> "We applied three core React performance patterns from Vercel's engineering guidelines:
> 1. **Component Memoization (`React.memo`)**: Wrapped `MessageItem` in `React.memo`. When new tokens stream into the active assistant message, React only repaints that single active message node; all historical messages skip re-rendering.
> 2. **Localized State Management**: Encapsulated stream consumption in a deep `useChat()` hook that updates message content using functional state updates (`setMessages(prev => prev.map(...))`), keeping callback references stable.
> 3. **Non-blocking Scroll Anchoring**: Used a dedicated bottom ref with safe optional chaining for smooth scrolling, preventing layout thrashing and ensuring graceful degradation in headless test environments (like jsdom)."

---

### Q4: How do you handle cold starts on serverless or free-tier hosting (like Render) without frustrating recruiters?
> **Answer**:
> "Render's free tier spins down containers after 15 minutes of idle time, taking ~25–33 seconds to boot on a cold request. If unhandled, recruiters will assume the site is broken and leave.
> 
> We solved this through proactive, transparent UX:
> 1. On page mount, the frontend fires a lightweight background health check to `GET /api/health`.
> 2. If the health check doesn't resolve within 2.5 seconds, the status pill dynamically switches from 'Connecting...' to an amber pulsing 'Waking Up (Render ~25s)' indicator with an explanatory banner.
> 3. Once the instance boots and returns HTTP 200, the pill switches to a green 'Ready' state.
> 4. Setting honest expectations upfront turns a hosting limitation into a professional display of engineering transparency."

---

## 4. Official Documentation & References

- [HTML Standard — Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [MDN Web Docs — Using Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [MDN Web Docs — Streams API ReadableStream](https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream)
- [Starlette Documentation — StreamingResponse](https://www.starlette.io/responses/#streamingresponse)
- [FastAPI Documentation — Custom Response Classes](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Groq SDK Documentation — Async Streaming](https://github.com/groq/groq-python)
