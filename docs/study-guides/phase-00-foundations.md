# Phase 0 Study Guide: Environment, Systems Architecture & Walking Skeleton

> **Purpose**: This guide provides the complete theoretical foundation, architectural rationale, code walkthrough, and technical interview preparation for everything built in Phase 0. Use this document for revision and technical placement interview prep.

---

## 1. Core Engineering Concepts & "Why"

### 1.1 The "Tracer Bullet" / Walking Skeleton Pattern
In production software engineering, a **walking skeleton** is a minimal, end-to-end implementation of the system that connects all architectural layers (frontend SPA $\rightarrow$ reverse proxy $\rightarrow$ ASGI web server $\rightarrow$ CI/CD $\rightarrow$ hosting platform) with zero business logic.
- **Why do this on Day 1?** Free-tier cloud deployments (Render, Vercel) harbor the highest concentration of environmental surprises: cross-origin restrictions (CORS), read-only container filesystems, ephemeral storage, differing Python/Node minor versions, and cold-start latencies. Discovering these on day one with an empty skeleton takes minutes to isolate; discovering them after writing 2,000 lines of LLM agent code leads to compounding debugging nightmares.

### 1.2 Web Server Protocols: WSGI vs. ASGI
To understand FastAPI and Uvicorn, you must understand Python's web server interfaces:

```
[ Traditional Python Stack (WSGI) ]
Client Request ──> Reverse Proxy (Nginx) ──> Gunicorn (Master) ──> Worker Process (Sync) ──> Flask / Django

[ Modern Async Python Stack (ASGI) ]
Client Request ──> Cloudflare / Render Proxy ──> Uvicorn (Single Async Process) ──> FastAPI (Async Event Loop)
```

- **WSGI (Web Server Gateway Interface - PEP 3333)**: Synchronous, single request-response per worker thread. If a request takes 5 seconds (e.g., waiting for an LLM response or streaming tokens), that worker thread is completely blocked. To serve 10 concurrent streaming users, you would need 10 separate OS processes or threads, consuming hundreds of megabytes of RAM.
- **ASGI (Asynchronous Server Gateway Interface)**: Designed for long-lived connections, WebSockets, and Server-Sent Events (SSE). An ASGI server (Uvicorn) runs an `asyncio` event loop on a single OS thread. When a request awaits I/O (such as Groq generating tokens or a database responding), the event loop yields execution and immediately handles incoming packets for other users.
- **Why a single Uvicorn worker on Render?**
  Render's free tier provides **512 MB of RAM and 0.1 CPU**. Running Gunicorn with multiple worker processes multiplies memory footprint proportionally (each Python runtime copies libraries, embeddings, and indices into memory). A single Uvicorn process leverages the cooperative multitasking of `asyncio`, keeping memory usage under 60 MB while handling dozens of concurrent requests.

---

## 2. Deep Dive: What Was Built & Line-by-Line Code Analysis

### 2.1 Backend Architecture

#### A. Centralized Settings (`backend/app/settings.py`)
```python
class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str | list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    ...
```
- **The Concept**: Environment variables should never be scattered across `os.getenv()` calls in random files. `pydantic-settings` validates, casts, and bundles all environment variables into a strongly-typed class at startup.
- **The Bug We Fixed & Lesson**: When a field is typed strictly as `list[str]`, Pydantic Settings expects a JSON string in the environment (e.g. `["http://..."]`). When Render passed `http://localhost:5173,https://...`, Pydantic's internal `json.loads()` threw `JSONDecodeError`. By declaring `CORS_ORIGINS: str | list[str]` and using an `@field_validator(..., mode="after")`, we made the parser robust to raw comma-separated strings, JSON arrays, and Python lists.
- **Dependency Injection**: `get_settings()` uses Python's `@lru_cache` so settings are instantiated once, yet can be overridden cleanly in test suites via FastAPI's `app.dependency_overrides`.

#### B. Request Tracing & Forwarded Headers (`backend/app/main.py`)
```python
@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id
    ...
```
- **X-Request-ID**: In distributed systems, requests travel through proxies, frontends, and backend microservices. Attaching a unique UUID to every request allows you to correlate a bug reported by a user with the exact error line in Render's log streams.
- **Client IP & Proxy Headers**: When running behind a reverse proxy (Render + Cloudflare), `request.client.host` would normally report the proxy's internal IP address, not the user's real IP. Running Uvicorn with `--proxy-headers --forwarded-allow-ips='*'` instructs Uvicorn to trust incoming `X-Forwarded-For` headers so our rate limiters in Phase 7 see the real client IP.

#### C. Cross-Origin Resource Sharing (CORS)
- **What CORS actually is**: CORS is a **browser security mechanism**, not a server firewall.
- **Why curl works when browsers fail**: When you run `curl`, no browser sandbox exists; `curl` prints whatever bytes the server returns. But when a website running on `https://aamirmk-portfolio.vercel.app` executes JavaScript `fetch("https://aamirmk-portfolio.onrender.com")`, the browser notices the scheme/domain differ. The browser intercepts the call and inspects the server's `Access-Control-Allow-Origin` response header. If the origin is not listed, the browser refuses to let your JavaScript read the response.
- **Preflight `OPTIONS` requests**: For requests that mutate data or send custom headers (like `X-Request-ID`), the browser sends an HTTP `OPTIONS` probe first. Our `test_cors_preflight_options_request` tests and verifies this exact browser behavior.

---

### 2.2 Frontend Architecture

#### A. Strict TypeScript Configuration (`frontend/tsconfig.app.json`)
- `strict: true`: Enables all strict type-checking options (`noImplicitAny`, `strictNullChecks`, etc.).
- `noUncheckedIndexedAccess: true`: Prevents accessing arbitrary indices of arrays or object maps without checking for `undefined`. This eliminates the classic `TypeError: Cannot read properties of undefined` in production.

#### B. Network Boundary Validation (`frontend/src/lib/api.ts`)
```typescript
const data = (await response.json()) as unknown;
if (
  typeof data === "object" &&
  data !== null &&
  "status" in data &&
  "ready" in data && ...
) {
  return data as HealthStatus;
}
throw new Error("Invalid response schema from health endpoint");
```
- **Why runtime checking?** TypeScript types only exist at compile time; they are completely erased in production JavaScript. If the backend changes its schema or returns an unexpected error object, blindly casting `as HealthStatus` causes runtime crashes in UI components. Explicit runtime type validation guarantees boundary safety.

#### C. React 19 Lifecycle Safety (`frontend/src/App.tsx`)
```typescript
useEffect(() => {
  const controller = new AbortController();
  ...
  return () => {
    controller.abort();
  };
}, []);
```
- **Why `AbortController`?** If the user navigates away or component unmounts while the 25-second cold start is resolving, the in-flight network request is aborted. This prevents memory leaks and state updates on unmounted components (`Can't perform a React state update on an unmounted component`).
- **Accessibility**: Using `aria-live="polite"` on the status container notifies screen readers whenever the connection status changes without jarring the user.

---

## 3. Placement & Interview Q&A (Prepare for Technical Rounds)

### Q1: "Walk me through how an asynchronous event loop handles concurrent requests in Python compared to multithreading or multiprocessing."
> **Answer**: 
> "In multithreading or multiprocessing, the operating system kernel is responsible for preemptive multitasking, switching execution between threads. Each OS thread has stack overhead (typically 8MB in Linux) and context switching incurs CPU cache invalidation costs.
> In contrast, an ASGI framework like FastAPI runs on an event loop (`asyncio`) on a single OS thread using cooperative multitasking. The event loop maintains a queue of ready tasks. When an endpoint hits an `await` expression (like an HTTP call to Groq or an async database query), it suspends execution and registers a callback with the OS selector (epoll/kqueue). Control returns immediately to the event loop, which picks the next ready task. This allows a single process on a constrained free instance (0.1 CPU, 512MB RAM) to maintain dozens of concurrent streaming SSE connections without thread overhead, provided no synchronous blocking calls monopolize the thread."

### Q2: "What is an HTTP Preflight request and when does a browser trigger it?"
> **Answer**:
> "An HTTP Preflight is an automatic `OPTIONS` request sent by the browser before the actual request when performing cross-origin communication. It asks the server for permission by sending headers like `Access-Control-Request-Method` and `Access-Control-Request-Headers`.
> Browsers trigger preflights for any request that is not 'simple'—meaning any request using HTTP methods other than GET, HEAD, or POST; requests using POST with Content-Types other than `application/x-www-form-urlencoded`, `multipart/form-data`, or `text/plain` (such as `application/json`); or requests containing custom headers like `X-Request-ID` or `Authorization`. If the server's `OPTIONS` response does not return an `Access-Control-Allow-Origin` matching the current web page, the browser drops the actual request and logs a CORS violation."

### Q3: "What is the difference between compile-time type safety in TypeScript and runtime validation, and why do both matter at API boundaries?"
> **Answer**:
> "TypeScript is a compile-time static type system that performs type erasure; all types and interfaces are stripped during compilation, emitting plain JavaScript. Compile-time types protect developers from logic errors within internal codebase boundaries.
> However, external data crossing the network boundary (HTTP responses, user inputs, database records) arrives at runtime where TypeScript cannot inspect it. If the API returns unexpected JSON or a 500 error page, a naive TypeScript cast (`res.json() as MyType`) creates a false sense of safety that leads to uncaught exceptions in UI rendering. True defensive programming pairs compile-time TypeScript with runtime boundary validation (such as manual type guards or schema libraries like Zod), verifying the payload shape before downstream components consume it."

---

## 4. Curated Official Reading List

1. **FastAPI Lifespan and Application Structure**:
   - [FastAPI: Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
   - [FastAPI: Events (Lifespan Context Managers)](https://fastapi.tiangolo.com/advanced/events/)
2. **Uvicorn & ASGI Specification**:
   - [ASGI Documentation](https://asgi.readthedocs.io/en/latest/)
   - [Uvicorn Deployment & Proxy Headers](https://www.uvicorn.org/deployment/)
3. **MDN Web Docs on Browser Security**:
   - [MDN: Cross-Origin Resource Sharing (CORS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
   - [MDN: Using the Fetch API with AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
4. **Pydantic & Modern Python Types**:
   - [Pydantic V2 Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
   - [PEP 604 – Allow writing union types as X | Y](https://peps.python.org/pep-0604/)
