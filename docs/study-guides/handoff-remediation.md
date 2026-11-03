# Handoff Remediation — Evidence, Failure, and Stream Lifecycles

Goal: explain why an apparently successful response can still violate the product's truth or completion contract. This sprint preserves the fixed FastAPI/Groq/React stack and changes the guarantees at existing interfaces.

## 1. Evidence identity is not evidence support

The old scorer received one set containing every retrieved chunk. If Python requirement A retrieved chunk X, AWS requirement B could cite X and remain strong. An ID existing somewhere in a request is weaker than that ID being retrieved for the requirement being scored.

Walk through `backend/app/fit/scorer.py`:

- `validate_and_downgrade_verdicts` accepts a mapping from requirement ID to allowed citation IDs.
- Inside the loop, `valid_chunk_ids.get(item.requirement.id, ())` selects only that requirement's evidence. Missing keys safely provide no evidence.
- The comprehension removes unrelated/unknown citations.
- Strong/partial without a surviving citation becomes gap; deterministic scoring then operates on the sanitized verdicts.

`pipeline.py` constructs this mapping beside `retrieved_by_req`. `models.py::unique_requirement_ids` rejects ambiguous identities before retrieval maps can overwrite entries. The scorer regression deliberately uses `python` as both an unrelated requirement ID and a cited chunk ID: the old global-key interpretation accepted it, while the new local lookup rejects it.

This is still provenance validation. A retrieved paragraph saying “no AWS use established” must not justify strong AWS experience. Semantic support, negative-fact constraints and unconstrained generated summaries remain separate work. An interview answer claiming “the model cannot overclaim” would still be inaccurate.

## 2. Curated assessments are not calibrated ground truth

`golden_benchmarks.py::_report` computes counts, tier and headline through `compute_fit_summary`, preventing hand-maintained arithmetic from drifting. Every cited ID is checked against the current public corpus in `test_fit_golden.py`. Narratives were reviewed against those facts; unsupported CKA/kind/k3s and active-AWS claims were removed. The UI discloses manual assessment provenance.

Working/learning exposure can justify a narrower partial match instead of strong expertise. Plans do not constitute hands-on experience. The three software-role snapshots now rate Partial Match; firmware stays Low Match. This reflects current curated evidence, which still requires resolution of draft approval and stale descriptions. No factual flags were silently promoted.

Placement Q&A: **Why not just replace every invalid ID with a real one?** Because that would repair referential integrity while leaving unsupported claims. Both the reference and the cited content matter.

## 3. Fail closed while preserving the user's job

`pipeline.py::_extract_requirements` permits two attempts. Invalid JSON, empty extraction, duplicate IDs or blank text cannot lead to a fabricated generic software requirement. After the retry, `RequirementExtractionError` reaches the specific handler in `run`, which emits `extraction_error`. Retrieval, judging, summary generation and cache insertion are never reached.

`llm.py::GroqLLM.complete` preserves JSON-mode text. Prose normalization previously changed `Python3. Strong API skills` into a string containing literal newlines, invalidating otherwise valid JSON. The adapter regression uses a mocked SDK response, not a real Groq request.

Placement Q&A: **Why retain a retry?** A model can produce a transient formatting failure. A single bounded retry allows recovery; it does not authorize inventing assessable requirements after both attempts fail. `test_extraction_can_recover_on_its_single_retry` locks down that distinction.

## 4. Separate domain text from transport control

`api/chat.py::StreamHeartbeat.PING` is an enum marker. Its identity, not a text prefix, tells callers that a heartbeat occurred. Thus `:` and `: contact` remain ordinary model tokens. Both chat turns and `api/fit.py::transport_stream` convert the marker to `: heartbeat\n\n`.

The architecture review found an important shared-caller regression: changing the wrapper's result type required updating fit as well as chat. Sending an enum directly to StreamingResponse failed on `.encode()`. A shortened-interval, delayed fake pipeline reproduces this through the actual fit endpoint. It now verifies heartbeat comments followed by completion.

Placement Q&A: **Why is `startswith(":")` wrong here?** A colon identifies comments only after text is encoded as SSE protocol lines. The LLM's domain text is not an SSE frame yet.

## 5. EOF is not application completion

`frontend/src/lib/sse.ts::readEventStream` owns reading, buffering and cleanup. `TextDecoder` retains partial UTF-8 bytes between chunks; `parseSSEBuffer` retains partial LF-delimited frames. Domain dispatchers return true only after handling a terminal event. The reader stops then; a network EOF before that event throws an error.

The `finally` block cancels the reader and releases its lock on success, failure or abort. An explicit AbortSignal remains a non-error path in the public clients. Reader cancellation and lock release are separate responsibilities: releasing a lock alone does not consume or cancel the underlying stream. See [MDN reader lifecycle](https://developer.mozilla.org/en-US/docs/Web/API/ReadableStreamDefaultReader/releaseLock) and the [SSE specification](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream).

`useStreamRecovery.test.ts` uses real hooks and real transport with mocked HTTP bodies. It proves an interrupted chat exits loading, marks the message as error and can successfully retry. Fit also exits loading and permits another request. Transport tests cover premature EOF, malformed/error terminal events and reader unlocking. Existing tests cover normal completion and explicit abort. CRLF parsing and a complete idle-timeout policy remain deferred.

## 6. Validation failure must remain a client error

`main.py` handles FastAPI request validation errors. Pydantic error context can contain a live `ValueError` object; JSONResponse cannot serialize that object. Filtering `ctx` from each detail preserves JSON-compatible field locations/messages and the request ID. The endpoint regression posts 50 spaces, verifying HTTP 422 rather than the reproduced 500. See [Pydantic error details](https://docs.pydantic.dev/latest/errors/errors/) and [FastAPI validation handlers](https://fastapi.tiangolo.com/tutorial/handling-errors/).

## Review evidence

Baseline: 239 backend/eval and 125 frontend tests. Sprint final backend run: `python -m pytest backend/tests evals -q` → **253 passed, 1 warning in 16.62s**. Frontend final run: `npm test` → **132 passed, 18 files, 17.48s**. Ruff lint passed; Ruff reports 60 files already formatted. ESLint and TypeScript passed. Final Vite build: 5.53s, **162.99 kB gzip JS**, CSS 7.57 kB gzip. Explicit Node/zlib assertion: **162,988 JS bytes < 200,000**. The existing AnyIO deprecation and Vite chunk/annotation warnings remain non-failing. No live Groq calls, production deployment checks or browser QA were performed. agent-browser is unavailable locally.

## Teach-back — answer before looking back

1. A requirement cites a real chunk retrieved for a different requirement. What happens now, and what additional question must we still ask about a surviving local citation?
2. A response streams several tokens and the connection closes without `done`. Why is that an error, and how does deliberate Stop differ?
3. Both extraction attempts fail. Which pipeline stages must not run, and why would a generic fallback requirement violate the product promise?

Teach-back completion is pending the user's answers. Ask follow-up questions about any concept that remains unclear.
