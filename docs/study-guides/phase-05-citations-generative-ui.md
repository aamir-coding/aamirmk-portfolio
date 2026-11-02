# Study Guide — Phase 5: Source Citations & Generative UI

> **Scope:** Server-supplied generative UI, function-calling seams, multi-event SSE streaming, verified receipt attribution, accessible dialog design, and strict bundle preservation.
> **Related Code:** `backend/app/tools/`, `backend/app/llm.py`, `backend/app/api/chat.py`, `frontend/src/components/Chat/SourceChips.tsx`, `frontend/src/components/Chat/ProjectCard.tsx`, `frontend/src/components/Chat/ProjectModal.tsx`, `frontend/src/lib/sse.ts`.

---

## 1. High-Level Architectural Concepts

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend (/api/chat)                     │
│                                                                        │
│  User Query ──► [Guardrails & Rate Limit]                              │
│                      │                                                 │
│                      ▼                                                 │
│             [Hybrid Retriever (top_k=4)] ──► Extracts SourceCitation[] │
│                      │                                                 │
│                      ▼                                                 │
│             [LLMClient Adapter Seam]                                   │
│             ├─ GroqLLM (with tools schema: show_project_card)          │
│             └─ FakeLLM (for deterministic test isolation)             │
│                      │                                                 │
│             (If tool called by LLM)                                    │
│                      │                                                 │
│                      ▼                                                 │
│             [ToolRegistry.execute()] ──► Resolves authoritative        │
│                                          ProjectCardData from disk     │
│                                                                        │
│  Output: reply text + sources[] + cards[]                              │
│  - Non-streaming: JSON body ChatResponse                               │
│  - Streaming: SSE frames (event: sources, event: card, event: token)   │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │ SSE / JSON
┌─────────────────────────────────▼──────────────────────────────────────┐
│                      React + TypeScript Frontend                       │
│                                                                        │
│  [streamChat / useChat] ──► MessageItem                                │
│                               ├─ Transcript Text & Cursor              │
│                               ├─ SourceChips (receipt links & popover) │
│                               └─ ProjectCard (dossier styling)         │
│                                       │ (Click "Inspect Architecture") │
│                                       ▼                                │
│                                 ProjectModal (<dialog>, focus trap,    │
│                                               accessible Esc listener) │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.1 The Problem with LLM-Generated UI
In naive generative UI implementations, applications ask the model to output raw JSON or HTML to render cards. This approach is fatal for portfolio and enterprise assistants:
1. **Hallucination of Metrics & Tech:** A generative model frequently hallucinates plausible-sounding metrics (e.g. claiming 99.9% uptime or 50,000 active users) or stacks that were never used.
2. **Broken URLs:** Models often output 404 links, malformed query params, or non-existent repository branches.
3. **High Latency & Token Wastage:** Generating large JSON structures takes hundreds of completion tokens, increasing TTFT (Time to First Token) and draining daily token quotas.

### 1.2 Design Principle 2: "The Model Selects, Your Server Supplies"
In this architecture:
- The LLM acts purely as a **router / selector**: it decides *whether* a project is relevant and outputs a structured tool call: `show_project_card(project_id="entropy-oj")`.
- The **backend server supplies** the immutable, verified `ProjectCardData` loaded directly from curated facts on disk.
- Result: **0% hallucination risk on generative UI cards**. Every metric, tech stack badge, live deployment link, and architectural blueprint is 100% authoritative and verified.

### 1.3 Design Principle 3: "Every Claim Has a Receipt"
Every assistant response is accompanied by `SourceCitation` receipts linking directly to the underlying questionnaire section codes (e.g. `[J1]`, `[X7]`, `[E1]`) and live external deployment/repository URLs.

---

## 2. Deep Module Seam Design & Tool-Calling Protocol

### 2.1 The ToolRegistry Seam (`app/tools/registry.py`)
Following deep module principles, `ToolRegistry` hides tool resolution, JSON string parsing, schema generation, and error handling behind a minimal two-method interface:
```python
class Tool(Protocol):
    name: str
    description: str
    def get_schema(self) -> dict[str, Any]: ...
    def execute(self, arguments: dict[str, Any]) -> Any: ...

class ToolRegistry:
    def get_schemas(self) -> list[dict[str, Any]]: ...
    def execute(self, name: str, arguments: dict[str, Any] | str) -> Any: ...
```

### 2.2 The Two-Turn Function Calling Loop
When tool calling is active:
1. **Turn 1 (Tool Selection):** The backend sends `messages` and `tools` to the LLM. If the model determines a project card is needed, it returns `finish_reason="tool_calls"` with `tool_calls=[ToolCall(name="show_project_card", arguments='{"project_id":"entropy-oj"}')]`.
2. **Execution:** The server resolves `get_project_card("entropy-oj")` from `PROJECT_CATALOG` and formats a `role="tool"` message confirming the card was summoned.
3. **Turn 2 (Synthesis):** The backend calls the LLM with the tool response in context, allowing the assistant to generate natural, conversational prose explaining the project alongside the summoned card.

---

## 3. Dual-Event SSE Streaming Architecture

Browser-native `EventSource` is limited to `GET` requests without custom body payloads. Our hand-built `streamChat` client (`frontend/src/lib/sse.ts`) streams over HTTP `POST` and parses distinct SSE event types:

| Event Type | Payload | Timing | Frontend Action |
|------------|---------|--------|-----------------|
| `event: sources` | `{"sources": [...]}` | Stream start | Immediately renders verified receipt chips |
| `event: card` | `{"card": {...}}` | Upon tool execution | Instantly mounts authoritative `ProjectCard` |
| `event: token` | `{"token": "..."}` | Real-time | Appends streaming transcript words with cursor |
| `event: done` | `{"conversation_id": "...", "sources": [...], "cards": [...]}` | Stream finish | Finalizes message state, removes active cursor |
| `event: error` | `{"detail": "..."}` | On exception | Displays graceful error notice |

---

## 4. Line-by-Line Codebase Tour

### 4.1 Backend Project Catalog (`backend/app/tools/projects.py`)
- `ProjectCardData`: Immutable Pydantic v2 model with `frozen=True`. Encapsulates `id`, `title`, `subtitle`, `summary`, `role`, `tech_stack`, `highlights`, `metrics`, `github_url`, `live_url`, `source_sections`, and `architecture_details`.
- `PROJECT_CATALOG`: Master dictionary containing all 8 verified projects (Entropy-OJ, AI Digital Assistant, Health Premium Predictor, HealthTracker, Keynone, VayuSetu, Browser Games, Secure Auction).
- `PROJECT_ALIASES`: Resilient lookup mapping model variants (`"entropy"`, `"insurance"`, `"healthtracker"`) to canonical project keys.

### 4.2 LLM Seam Protocol (`backend/app/llm.py`)
- `ToolCall`: Frozen dataclass capturing `id`, `name`, and serialized `arguments`.
- `Message`: Extended to support `tool_calls` on assistant messages and `tool_call_id` on tool role messages.
- `GroqLLM.stream()`: Accumulates streaming delta chunks (`delta.tool_calls[i]`) across index buffers, yielding `ToolCall` value objects upon stream completion while yielding `str` tokens in real-time when no tools are called.
- `FakeLLM`: Simulates tool calling deterministically when configured with `tool_calls=[...]`, enabling 0 API cost and sub-second CI execution.

### 4.3 Chat Endpoints (`backend/app/api/chat.py`)
- `extract_citations()`: Deduplicates retrieved `RetrievedChunk` items by `chunk_id` into compact `SourceCitation` schemas.
- `POST /api/chat`: Orchestrates non-streaming two-turn tool dispatch and attaches `sources` and `cards` to `ChatResponse`.
- `POST /api/chat/stream`: Emits `event: sources` early, checks for `ToolCall` items during stream, yields `event: card`, streams Turn 2 explanation tokens, and concludes with `event: done`.

### 4.4 Frontend Components (`frontend/src/components/Chat/`)
- `SourceChips.tsx`: Renders compact editorial chips with questionnaire section codes (`[J1]`, `[X7]`) and external receipt links with `target="_blank"` and `rel="noopener noreferrer"`.
- `ProjectCard.tsx`: Distinctive dossier layout with role badges, verified tags, tech stack pills, metric cells, and "Inspect Architecture →" trigger.
- `ProjectModal.tsx`: Accessible dialog featuring:
  - Focus trap: isolates Tab navigation within modal.
  - Escape key listener: closes dialog smoothly.
  - Body scroll lock: sets `overflow: hidden` on mount and restores on unmount.
  - Focus restoration: returns focus to the invoking button upon dismissal.
  - ARIA attributes: `role="dialog"`, `aria-modal="true"`, `aria-labelledby="modal-project-title"`.

---

## 5. Technical Interview Questions & Answers

### Q1: Why not let the LLM generate the JSON for the project card directly in the chat stream?
**Answer:** Letting the LLM generate UI card JSON directly introduces severe hallucination risks, latency penalties, and fragile error parsing:
1. **Hallucination:** An LLM may alter critical verified metrics (e.g. inventing accuracy numbers or test counts) or invent GitHub URLs that lead to 404s.
2. **Validation Failures:** Streaming JSON is prone to syntax truncation if the stream drops or token limits are hit, causing UI rendering crashes.
3. **Architectural Separation:** By adhering to Design Principle 2 ("The model selects, your server supplies"), the LLM is only entrusted with intent classification (which project to summon), while our backend supplies authoritative, immutable data from verified files.

### Q2: How does the streaming tool-calling loop handle queries that do NOT need a project card without adding latency?
**Answer:** In `GroqLLM.stream()`, `tools` are passed to Groq's completions endpoint with `tool_choice="auto"`. When a query does not mention a project (e.g. "Where is Aamir located?"):
1. Groq immediately yields `delta.content` chunks with text tokens.
2. The SSE generator immediately emits `event: token` frames with 0 added latency (~400-500ms TTFT).
3. No tool calls are emitted, and the stream concludes in a single turn without incurring a second LLM round-trip.

### Q3: How is keyboard accessibility (a11y) enforced in the architectural modal without third-party dependencies?
**Answer:** Rather than pulling in heavy modal libraries (e.g. `@radix-ui/react-dialog` or `floating-ui`) which inflate the client bundle, `ProjectModal.tsx` implements accessible dialog primitives natively:
1. **Focus Trapping:** On mount, it queries all focusable elements (`button, [href], input, etc.`). A `keydown` listener intercepts `Tab` and `Shift+Tab`: when tabbing past the last element, focus loops to the first; when shift-tabbing past the first, it loops to the last.
2. **Escape Listener:** Listens for `e.key === "Escape"` to trigger `onClose()`.
3. **Focus Restoration:** Captures `document.activeElement` prior to opening and restores focus to that exact invoking button when unmounted.
4. **ARIA:** Declares `role="dialog"`, `aria-modal="true"`, and links the header via `aria-labelledby`.

---

## 6. Official Documentation & References

- [Groq API Tool Calling Guide](https://console.groq.com/docs/tool-use)
- [OpenAI Function Calling Specification](https://platform.openai.com/docs/guides/function-calling)
- [MDN: Using Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [W3C WAI-ARIA Dialog (Modal) Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [Vercel React Performance Best Practices](https://vercel.com/blog)
