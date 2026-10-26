# Phase 1 Study Guide: FastAPI Chat Endpoint, Async LLM Seam & Grounded Prompting

> **Purpose**: This guide provides the complete theoretical foundation, architectural rationale, line-by-line code connections, and placement interview preparation for everything built in Phase 1 (`phase-1-chat`). Use this document for technical revision and AI/backend engineering interviews.

---

## 1. Core Engineering Concepts & "Why"

### 1.1 The Deep Module & Test Isolation via Protocol Seams
In AI software engineering, relying on third-party cloud APIs (like Groq, OpenAI, Anthropic) introduces significant challenges:
- **Non-determinism**: LLM completions vary across calls.
- **Latency & Flakiness**: Cloud network roundtrips take 500ms–2000ms.
- **Cost & Quota**: Running test suites on every save or in CI burns free-tier rate limits (Groq's 8,000 TPM / 1,000 RPD).
- **Secrets in CI**: Requiring live API keys in CI/CD pipelines risks leaking credentials.

To solve this, we applied the **Deep Module pattern** (*John Ousterhout, A Philosophy of Software Design*) and **Seam Discipline** (*Michael Feathers, Working Effectively with Legacy Code*):

```
┌────────────────────────────────────────────────────────┐
│              FastAPI Route (/api/chat)                 │
└───────────────────────────┬────────────────────────────┘
                            │ Depends(get_llm_client)
                            ▼
┌────────────────────────────────────────────────────────┐
│            LLMClient (Protocol Interface)              │
│       complete(messages) -> AssistantMessage           │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
         Production                      Test
                ▼                        ▼
┌───────────────────────────────┐ ┌──────────────────────┐
│            GroqLLM            │ │       FakeLLM        │
│  - Wraps AsyncGroq            │ │  - In-memory         │
│  - Handles retry / timeouts   │ │  - Instant (0.01ms)  │
│  - Maps SDK errors to domain  │ │  - Captures messages │
│  - Extracts token usage       │ │  - Zero API credits  │
└───────────────────────────────┘ └──────────────────────┘
```

- **Protocol vs. Abstract Base Class (ABC)**: Python's `typing.Protocol` uses **structural subtyping (duck typing)** rather than nominal inheritance (`class GroqLLM(ABC)`). An adapter satisfies the seam simply by implementing `async def complete(messages: list[Message]) -> AssistantMessage:`. It requires no shared base class, keeping the coupling minimal.
- **Why a Fake instead of Mocks (unittest.mock)?**:
  - `unittest.mock.patch` couples tests to internal method names and call paths of the implementation. If you rename `client.chat.completions.create`, mocks silently break or pass falsely.
  - `FakeLLM` is a real working in-memory implementation of `LLMClient`. Tests verify actual state (e.g. `fake.last_messages` received both system prompt and user message) through the exact same public interface the router uses.

### 1.2 Asynchronous I/O with Groq: `AsyncGroq` & Event Loops
FastAPI runs on an ASGI server (Uvicorn) with a single Python process running an asynchronous event loop (`asyncio`).

- **Synchronous Client (The Anti-Pattern)**:
  If an endpoint uses the synchronous `Groq()` client:
  ```python
  response = client.chat.completions.create(...)  # BLOCKS THE OS THREAD
  ```
  The entire Python process halts for the 1.5 seconds it takes Groq to return tokens. During those 1.5 seconds, no other user request can be processed. 10 concurrent requests would serialize to 15 seconds!
- **Asynchronous Client (`AsyncGroq`)**:
  `AsyncGroq` uses `httpx.AsyncClient` under the hood with non-blocking socket I/O.
  ```python
  response = await self._client.chat.completions.create(...)  # YIELDS TO EVENT LOOP
  ```
  When `await` is hit, Uvicorn's event loop pauses the current coroutine, registers the socket file descriptor with the OS kernel (`epoll` on Linux, `IOCP` on Windows), and immediately begins handling other incoming HTTP requests. When Groq sends back the HTTP response packets, the event loop resumes the coroutine.

### 1.3 Context Stuffing vs. Full RAG (Phase 1 Baseline)
Before building hybrid retrieval (BM25 + embeddings) in Phase 2, we established an authoritative baseline: **Context Stuffing**.
- **What is Context Stuffing?**: Injecting the entire curated résumé markdown document directly into the LLM's system prompt on every request.
- **Token Arithmetic**:
  - Aamir's complete résumé in clean markdown: ~1,100 tokens.
  - System prompt instructions & persona constraints: ~280 tokens.
  - Total prompt overhead: **~1,380 tokens**.
  - User query + response: ~200 tokens.
  - Total per-request: ~1,580 tokens.
- **Why this is the right Phase 1 decision**:
  1. Groq's `openai/gpt-oss-120b` free tier limit is **8,000 TPM** (Tokens Per Minute). 1,580 tokens allows 5 full requests per minute without any chunking.
  2. The LLM has 100% global document visibility: it cannot miss a bullet point due to retrieval recall errors or chunk boundary fragmentation.
  3. Provides an instant baseline against which Phase 2's retrieval accuracy can be rigorously measured.

---

## 2. Line-by-Line Code Walkthrough & Architectural Seams

### 2.1 The LLM Adapter (`backend/app/llm.py`)

#### Value Objects
```python
@dataclass(frozen=True, slots=True)
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str

@dataclass(frozen=True, slots=True)
class AssistantMessage:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
```
- `frozen=True`: Guarantees immutability. Messages cannot be accidentally mutated during pipeline execution.
- `slots=True`: Prevents creation of internal `__dict__`, reducing memory allocation per object and speeding up attribute access in high-throughput loops.

#### Domain Exception Hierarchy
```python
class LLMError(Exception):
    """Base error for all LLM-related failures."""

class LLMRateLimitError(LLMError): ...
class LLMAuthError(LLMError): ...
class LLMUnavailableError(LLMError): ...
```
- **Why Domain Exceptions?**: The rest of the application should never import `groq.RateLimitError` or `groq.AuthenticationError`. If we switch providers or add local models in the future, the router logic remains unchanged because it only knows about our internal `LLMError` hierarchy.

#### The Dependency Seam
```python
class LLMClient(Protocol):
    async def complete(self, messages: list[Message]) -> AssistantMessage: ...

def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    return GroqLLM(settings)
```
- `get_llm_client` serves as the FastAPI dependency provider. In tests, `app.dependency_overrides[get_llm_client] = lambda: FakeLLM(...)` swaps the production client for an in-memory test double without altering production routes.

---

### 2.2 System Prompt & Negative Constraints (`backend/app/prompts/`)

#### The Third-Person Identity
```text
You are an AI assistant built to answer questions about Aamir Mohammed Khan.
You speak in the third person — you talk *about* Aamir, never *as* Aamir.

Your identity: "I'm an AI assistant trained on Aamir's verified résumé, projects, and experience."
```
- **Rationale**: Impersonating the candidate creates an uncanny valley and ethical distrust with recruiters. Speaking in the third person establishes transparency and professional grounding.

#### Explicit Negative Constraints & Fallback Rules
```text
1. Only use the facts provided below. Never invent qualifications...
2. If the context does not contain an answer, say so honestly. Offer to forward the question to Aamir.
5. No private information. Do not share phone numbers, addresses...
```
- **Verified Behavior**: When queried `"Does Aamir have experience with Rust and Kubernetes?"`, the model replied:
  > *"Aamir’s résumé does not list Rust or Kubernetes among his technical skills or project experience... If you would like Aamir to clarify whether he has informal exposure to these technologies, I can forward the question to him."*
  Zero hallucination, polite honesty, and clear candidate representation.

---

### 2.3 Strict Domain Models (`backend/app/models.py`)

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None)
    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("message")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message cannot be empty or whitespace only")
        return trimmed
```
- **Defensive Boundary Rules**:
  - `str_strip_whitespace=True`: Removes leading and trailing whitespace automatically.
  - `min_length=1` + `validate_non_empty`: Prevents empty queries or blank lines from hitting the LLM and wasting tokens.
  - `max_length=2000`: Protects against token exhaustion attacks and unbounded prompt stuffing by malicious users.

---

### 2.4 The Router & Error Translation (`backend/app/api/chat.py`)

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    llm: LLMClient = Depends(get_llm_client),
) -> ChatResponse:
    conv_id = request.conversation_id or uuid.uuid4().hex
    messages = [
        Message(role="system", content=SYSTEM_PROMPT),
        Message(role="user", content=request.message),
    ]
    try:
        completion = await llm.complete(messages)
    except LLMRateLimitError as exc:
        raise HTTPException(status_code=429, detail="Rate limit reached...") from exc
    except LLMAuthError as exc:
        raise HTTPException(status_code=500, detail="LLM authentication failure...") from exc
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail="AI service is currently unavailable...") from exc
```
- Translates lower-level domain exceptions into standardized HTTP status codes (`429`, `500`, `503`).
- All errors are formatted into our unified JSON envelope by the `main.py` exception handlers, with `request_id` preservation for end-to-end tracing.

---

## 3. Measured Benchmarks & Verification Evidence

### 3.1 Live Groq Integration Smoke Test
- **Model**: `openai/gpt-oss-120b` (hosted on Groq LPU inference engine)
- **Status**: `200 OK`
- **End-to-End Latency**: **1,536 ms** (~1.5s total roundtrip)
- **Token Breakdown**:
  - Prompt Tokens: **1,381** (System prompt + context-stuffed résumé)
  - Completion Tokens: **150**
  - Total Tokens: **1,531**
- **Rate Limit Headroom**: 1,531 tokens consumed against the 8,000 TPM limit (19.1% of 1-minute capacity).

---

## 4. Technical Placement & Senior Engineering Q&A

### Q1: How do you prevent unit and integration tests from hitting real third-party AI APIs?
> **Answer**: By implementing the Dependency Inversion Principle using a Protocol seam. We created an `LLMClient` protocol with a single `complete(messages)` method. In production, FastAPI injects `GroqLLM` which wraps the real `AsyncGroq` SDK. In tests, we override the dependency using `app.dependency_overrides[get_llm_client] = lambda: FakeLLM()`. The `FakeLLM` returns deterministic canned responses and records incoming messages in-memory. This enables the entire 40-test suite to execute in **0.42 seconds** in CI without requiring API keys, incurring cloud charges, or failing due to upstream network hiccups.

### Q2: What is the difference between a Mock, a Stub, and a Fake?
> **Answer**:
> - **Stub**: Provides hardcoded answers to calls made during the test, usually not responding to anything outside what's programmed for the test.
> - **Mock**: An object pre-programmed with expectations which form a specification of the calls they are expected to receive. Verifies interactions (e.g. `mock.assert_called_once_with(...)`).
> - **Fake**: A working implementation that takes shortcuts not suitable for production (e.g., an in-memory database or an in-memory `FakeLLM`). It has real state and satisfies the interface completely, enabling behavior-driven testing rather than implementation-coupled testing.

### Q3: Why use FastAPI `Depends` instead of importing a global `llm_client` instance?
> **Answer**: Global instances introduce tight coupling and make concurrent test isolation difficult. With dependency injection via `Depends`:
> 1. The router is decoupled from client instantiation; it only declares what it needs (`LLMClient`).
> 2. Test suites can replace the dependency per test or test module without monkey-patching Python globals.
> 3. Lifecycle and configuration (e.g., retrieving fresh credentials from `Settings`) are handled centrally and lazily.

### Q4: Why did you choose context stuffing for Phase 1 instead of jumping directly to vector embeddings?
> **Answer**: Context stuffing is the simplest thing that could possibly work. Aamir's résumé is approximately 1,100 tokens. Groq's free tier allows 8,000 tokens per minute. Stuffing the résumé into the system prompt costs ~1,380 prompt tokens, providing 100% recall with zero retrieval latency and zero indexing overhead. Building this first allowed us to validate the prompt engineering, third-person persona, negative constraints, and API error handling before adding the complexity of chunking, vector embeddings, BM25 indices, and similarity search in Phase 2.

### Q5: How do you protect an LLM endpoint against Denial of Service and Token Exhaustion attacks?
> **Answer**: Through layered defense:
> 1. **Schema Validation**: Setting `max_length=2000` on inbound query strings in Pydantic drops oversized payloads at the HTTP layer (422) before LLM invocation.
> 2. **Token Caps**: Passing `max_completion_tokens=1024` to `AsyncGroq` prevents runaway generation costs.
> 3. **Error Translation & Rate Limiting**: Catching upstream 429s and translating them to client-facing HTTP 429 responses with retry guidance.

---

## 5. Official References & Further Reading

- [Groq Official Documentation - Python Async SDK](https://console.groq.com/docs)
- [FastAPI Dependency Injection Guide](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic V2 Models and Validators](https://docs.pydantic.dev/latest/concepts/models/)
- [Michael Feathers - Working Effectively with Legacy Code (Seams Pattern)](https://pepa.holla.cz/wp-content/uploads/2016/10/Working-Effectively-with-Legacy-Code.pdf)
- [John Ousterhout - A Philosophy of Software Design (Deep Modules)](https://web.stanford.edu/~ouster/cgi-bin/book.php)
