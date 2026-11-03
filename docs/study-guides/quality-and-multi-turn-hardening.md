# Study Guide — Quality & Multi-Turn Hardening: Conversational Coreference, Token Normalization, and Non-Destructive Navigation

> **Scope:** Multi-turn conversational RAG, coreference resolution via utility query rewriter (`openai/gpt-oss-20b`), tokenizer whitespace normalization (`\u202f`), markdown formatting repair layers, and decoupled view state machines.
> **Related Code:** `backend/app/retrieval/rewriter.py`, `backend/app/api/chat.py`, `backend/app/llm.py`, `backend/app/models.py`, `frontend/src/components/Chat/FormattedMessage.tsx`, `frontend/src/App.tsx`, `frontend/src/hooks/useChat.ts`, `frontend/src/lib/sse.ts`.

---

## 1. High-Level Architectural Concepts

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Client (React 19 + TypeScript)                        │
│                                                                                 │
│  User types: "tell me more"                                                     │
│      │                                                                          │
│      ▼                                                                          │
│  [useChat Hook] Extracts completed transcript:                                  │
│      history = [                                                                │
│        { role: "user", content: "what about entropy in one line" },             │
│        { role: "assistant", content: "Entropy-OJ is a full-stack..." }          │
│      ]                                                                          │
│      │                                                                          │
│      ▼ POST /api/chat/stream { message: "tell me more", history: [...] }        │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────────┐
│                            FastAPI Backend Pipeline                             │
│                                                                                 │
│  [Heuristic Follow-Up Gate] is_likely_follow_up("tell me more", history)        │
│      ├─ False (Self-contained) ──► Raw Query                                    │
│      └─ True  (Needs Context)  ──► [Query Rewriter] (openai/gpt-oss-20b)        │
│                                           │                                     │
│                                           ▼                                     │
│         Rewritten Query: "Entropy-OJ architecture and debugging features"       │
│                                           │                                     │
│                                           ▼                                     │
│  [Hybrid Retrieval] retriever.retrieve(search_query, top_k=4)                   │
│      ├─ BM25 Token Matching on "Entropy-OJ architecture..."                     │
│      └─ FastEmbed ONNX Cosine Dot Products                                      │
│      └─ Reciprocal Rank Fusion (k=60) ──► Chunks [proj-entropy-oj-*]            │
│                                           │                                     │
│                                           ▼                                     │
│  [LLM Message Construction]                                                     │
│      messages = [                                                               │
│        System(rules + retrieved_chunks),                                        │
│        User("what about entropy in one line"),                                  │
│        Assistant("Entropy-OJ is a full-stack..."),                              │
│        User("<user_inquiry>tell me more</user_inquiry>")                        │
│      ]                                                                          │
│                                           │                                     │
│                                           ▼                                     │
│  [Groq LLM Streaming] (openai/gpt-oss-120b)                                     │
│      └─► [normalize_llm_text] Sanitizes \u202f, \u00a0, \u200b                 │
│      └─► SSE event: token frames                                                │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────────┐
│                           Client Markdown Hardening                             │
│                                                                                 │
│  [FormattedMessage]                                                             │
│      ├─ Pre-normalizes Unicode whitespace artifacts                             │
│      ├─ Repairs unclosed bold list tags: "- **Email aamir..." ──► "- **Email:**"│
│      ├─ Protocol restoration: "https.linkedin.com" ──► "https://linkedin.com"   │
│      └─ Clickable bold link handler: "**https://...**" ──► <strong><a/></strong>│
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Engineering Problems Analyzed

### A. The Coreference Resolution Collapse in Conversational RAG
In single-turn RAG, the user's input string is assumed to be self-contained:
$$\text{Query} \xrightarrow{\text{retrieve}} \text{Chunks} \xrightarrow{\text{generate}} \text{Answer}$$

However, in multi-turn dialogues, human communication is inherently elliptical:
- Turn 1: *"What about Entropy in one line?"*
- Turn 2: *"Tell me more"*
- Turn 3: *"What was its stack?"*

If `"tell me more"` is fed directly into BM25 or dense embedding search:
1. **Lexical Collapse**: `"tell"` and `"more"` appear in nearly every chunk or no technical chunk, scoring near zero IDF.
2. **Dense Vector Drift**: The vector representation of `"tell me more"` clusters with generic conversational greetings or prompts, completely detaching from the previous topic (Entropy-OJ).
3. **Retrieval Miss**: The retrieval engine returns irrelevant chunks (e.g. general profile summaries).
4. **Generation Blindness**: Without the previous dialogue turns in the LLM's message history, the model cannot deduce what "it" or "more" refers to.

**The Solution:** Decouple the **search query** from the **generation prompt**:
- The **search query** is rewritten into a standalone keyword-rich query using the utility model (`openai/gpt-oss-20b`).
- The **generation prompt** receives the full rolling conversation history (`history_messages`), preserving natural conversational continuity.

---

### B. Open-Weight Model Tokenizer Artifacts (`\u202f`)
Open-weight models (including Llama-based and GPT-OSS checkpoints) trained on multilingual web corpora frequently exhibit punctuation and whitespace quirks:
1. **Narrow No-Break Space (`\u202f`, Unicode 8239)**:
   In French and certain typesetting standards, a narrow non-breaking space is grammatically placed before colons (`:`), semicolons, or between digit groupings (`+91\u202f89048\u202f16279`).
2. **Missing Closing Markdown Delimiters**:
   When the model emits `**Email\u202faamirmkh25@gmail.com`, it substitutes `\u202f` for the colon and drops the closing `**`. Standard markdown parsers expecting complete `**bold**` pairs fail, rendering raw asterisks.
3. **Protocol Stripping**:
   Models sometimes drop `://` and emit `https.linkedin...` or `httpswww.linkedin...`.

**The Solution:** Defense-in-depth across three layers:
1. **System Prompt Invariant (Rule 9)**: Explicit negative and few-shot formatting rules in `system.txt`.
2. **Backend Adapter Normalization**: `normalize_llm_text()` in `app.llm` translates `\u202f`, `\u00a0`, and `\u200b` into standard ASCII spaces `' '` across both streaming and complete calls.
3. **Client-Side Resilient Tokenizer**: `FormattedMessage.tsx` repairs unclosed bold contact items and restores protocol prefixes on malformed domain strings.

---

### C. SPA View Routing vs. Session Data Lifecycle
In Phase 4, the Editorial Dossier UI defined:
```tsx
// Anti-pattern: coupling view state to data emptiness
const isCoverState = messages.length === 0;
```
To let a visitor return to the Dossier Overview, the button was bound to `resetChat()`, destroying active conversation state and wiping `sessionStorage`.

**The Solution:** Strict separation of view state and transcript state:
- `viewMode: "cover" | "chat"` governs UI layout.
- `messages: ChatMessage[]` governs conversation history.
- `← Dossier Overview` sets `viewMode = "cover"` non-destructively.
- When `viewMode === "cover"` and `messages.length > 0`, a `Resume Chat (N) →` entry point appears in the header.
- `Clear Chat` explicitly resets the session only when requested.

---

## 3. Code Walkthrough

### 1. Follow-Up Query Rewriter (`backend/app/retrieval/rewriter.py`)
```python
def is_likely_follow_up(query: str, history: list[ChatHistoryMessage]) -> bool:
    if not history:
        return False
    trimmed = query.strip()
    words = trimmed.split()
    if len(words) <= 4:
        return True
    lower = trimmed.lower()
    if "aamir" in lower and not re.search(
        r"\b(that|it|its|the project|the app|the tool|more details|expand)\b",
        trimmed,
        re.I,
    ):
        return False
    return bool(_FOLLOW_UP_PATTERN.search(trimmed))
```
- Short queries ($\le 4$ words) or queries with pronouns trigger the rewriter.
- Queries explicitly about "Aamir" without relative pronouns bypass the rewriter to save latency and token quota.

### 2. Rewriting Execution with Utility Model
```python
async def rewrite_follow_up_query(
    query: str,
    history: list[ChatHistoryMessage],
    llm: LLMClient,
    model: str | None = None,
) -> str:
    if not is_likely_follow_up(query, history):
        return query

    recent = history[-4:]
    history_text = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in recent)
    user_prompt = f"Chat History:\n{history_text}\n\nFollow-up Question: {query}\n\nStandalone Search Query:"
    ...
```
- Restricts history to the last 4 messages (2 conversational turns) to keep token consumption minimal.
- Gracefully returns original `query` if the LLM times out or encounters rate limits.

---

## 4. Technical Placement Q&A

### Q1: How do you handle multi-turn conversations in a RAG system where the vector database index is built on static documents?
> **Answer:**  
> "In conversational RAG, the query sent to the retrieval index must be decoupled from the generation context sent to the LLM. 
> 
> If a user asks a follow-up like 'What was its tech stack?', querying a hybrid or dense index directly with 'What was its tech stack?' produces complete semantic failure because it lacks noun anchors. 
> 
> We implement a 2-step architecture:
> 1. **Coreference Query Rewriting**: When conversation history exists, a lightweight utility model (`openai/gpt-oss-20b`) transforms elliptical questions into self-contained search queries (e.g., 'What was its tech stack?' $\to$ 'Tech stack of Entropy Online Judge'). We gate this with a regex heuristic to prevent unnecessary LLM calls on self-contained queries.
> 2. **Multi-Turn Context Ingestion**: The retrieved documents are placed into the system prompt, and the rolling chat history (last 2–3 turns) is passed as standard conversational turns to the primary model (`openai/gpt-oss-120b`), allowing it to answer with full awareness of the dialogue transcript."

### Q2: Why keep the backend stateless for chat history instead of storing sessions in Redis or Postgres?
> **Answer:**  
> "For our portfolio architecture, keeping the server stateless offers three distinct advantages:
> 1. **Scalability & Resiliency**: The server has no ephemeral session state tied to a container. If Render spins down or restarts, active client sessions are not corrupted because the client persists history in `sessionStorage` and transmits the rolling window on each POST.
> 2. **Zero Database Cold-Start Latency**: Before Phase 9, our backend operates completely database-free. Eliminating session writes removes a database roundtrip from the critical streaming path.
> 3. **Controlled Token Windows**: By having the client send history and the server enforce a hard ceiling (e.g., last 6 messages, capped at 4,000 characters), the server deterministically bounds prompt token expenditure against daily free-tier quotas."

### Q3: How do you handle open-source model tokenizer quirks in production streaming applications?
> **Answer:**  
> "Open-weight models often leak tokenizer artifacts from multilingual pre-training data—for example, Unicode `\u202f` (Narrow No-Break Space) before colons or within digit groupings, unclosed markdown tags, or stripped `https://` prefixes.
> 
> In streaming applications, these quirks cannot be solved by a simple monolithic post-processor because tokens arrive incrementally chunk by chunk. We apply a multi-tier defense:
> 1. **System Prompt Invariants**: Negative constraints and explicit formatting rubrics instructing the model on exact output syntax.
> 2. **Streaming Delta Normalization**: A lightweight string transformer in the LLM adapter seam (`normalize_llm_text`) that normalizes non-standard Unicode whitespace (`\u202f`, `\u00a0`, `\u200b`) into standard ASCII spaces as each delta chunk yields from the generator.
> 3. **Client-Side Defensive Parsing**: A resilient markdown block and inline parser that repairs unclosed bold contact list items and recovers missing URL protocols prior to DOM rendering."

### Q4: How should single-page applications handle view navigation without corrupting active conversational state?
> **Answer:**  
> "View routing must be decoupled from data persistence. In early prototypes, developers often use data emptiness (`messages.length === 0`) as a proxy for the 'Landing / Cover' state, which inadvertently couples returning to the landing page with clearing the chat transcript.
> 
> In a production SPA, view mode (`viewMode: 'cover' | 'chat'`) should be an independent state machine. When a recruiter clicks '← Dossier Overview', the app switches `viewMode` to `'cover'` while retaining the messages in memory and `sessionStorage`. In the dossier view, a prominent 'Resume Chat (N) →' badge allows one-click resumption, while an explicit 'Clear Chat' button provides intentional session resets."

---

## 5. Official References & Documentation
- [FastAPI Request Body Models](https://fastapi.tiangolo.com/tutorial/body/)
- [Pydantic v2 String Constraints & Field Validation](https://docs.pydantic.dev/latest/concepts/fields/)
- [Unicode Character U+202F (Narrow No-Break Space)](https://www.unicode.org/charts/PDF/U2000.pdf)
- [Query Rewriting for Retrieval-Augmented Generation (Lewis et al.)](https://arxiv.org/abs/2005.11401)
