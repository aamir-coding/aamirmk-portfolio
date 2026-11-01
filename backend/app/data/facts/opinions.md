---
id: "opinion-fastapi-react-db"
type: "opinion"
title: "Why FastAPI & React; MongoDB vs PostgreSQL"
source_section: "O1"
tags: ["opinion", "architecture", "fastapi", "react", "mongodb", "postgresql", "databases"]
draft: true
private: false
---

Aamir's view on FastAPI and React: FastAPI fits Python backend work when typed request/response schemas, Pydantic validation, and an asynchronous API workflow are required. React supports a component-based interactive frontend that can evolve independently from backend services.

On database selection (MongoDB vs PostgreSQL): MongoDB fits document-shaped data and rapidly evolving records where flexibility is primary. PostgreSQL is the superior default when relationships, relational integrity constraints, and multi-table transactions are central. Aamir chooses databases based on the specific data model and query access patterns rather than treating one database as universally superior.

---
id: "opinion-rag-vs-finetuning"
type: "opinion"
title: "RAG vs Fine-Tuning vs Long Context"
source_section: "O2"
tags: ["opinion", "ai", "rag", "fine-tuning", "long-context", "llm-architecture"]
draft: true
private: false
---

Aamir's approach to grounding LLMs:
- **RAG (Retrieval-Augmented Generation):** Ideal when answers need current, changing, or verifiable information grounded in an approved knowledge base. It allows updating source documents without expensive retraining, provides verifiable source citations, and supports honest abstention. The trade-off is retrieval sensitivity (noisy chunks or missed context).
- **Fine-Tuning:** Useful for adapting style, tone, format, or specialized task patterns when a consistent training dataset and evaluation harness exist. Aamir would not use fine-tuning as the default mechanism for storing mutable factual knowledge.
- **Long Context:** Feasible when the source document set is small and latency/cost trade-offs are acceptable, but large context windows do not eliminate the necessity of selecting trustworthy evidence.

---
id: "opinion-production-debugging"
type: "opinion"
title: "Production Debugging Methodology"
source_section: "O3, H25"
tags: ["opinion", "debugging", "distributed-systems", "methodology", "observability"]
draft: true
private: false
---

Aamir's debugging process:
1. Start with observed symptoms versus expected behavior; reproduce the issue whenever possible.
2. Trace the entire request path by inspecting logs, timestamps, state, and network metrics across component boundaries.
3. Form a testable hypothesis before altering code, rather than jumping to conclusions based on the most visible symptom.
4. Apply the smallest reasonable change to address the root cause.
5. Validate the original failure scenario and check for regressions in nearby components.
6. Document remaining uncertainties and add monitoring or tests to prevent recurrence.

In Entropy-OJ, correlating API enqueue logs with worker activity showed a 2-minute-12-second delay and a Redis `ETIMEDOUT`, proving the issue was a socket timeout between services, not a compiler or VM performance problem.

---
id: "opinion-testing-philosophy"
type: "opinion"
title: "Testing Philosophy"
source_section: "O4"
tags: ["opinion", "testing", "quality", "unit-tests", "integration-tests", "evals"]
draft: true
private: false
---

Aamir's testing principles:
- Tests must verify intended behavior, edge cases, and failure recovery, not merely mirror implementation details.
- Fast, deterministic unit tests for core logic, integration tests for service and network boundaries, and end-to-end checks for critical user journeys.
- For AI features: automated evaluation suites with labeled query datasets, source faithfulness checks, adversarial prompts, and explicit abstention testing.
- AI-generated tests must always be reviewed and executed. The mere presence of test files in a repository does not constitute verification; only executed tests with observed results count as evidence.

---
id: "opinion-system-design"
type: "opinion"
title: "System Design Principles (Entropy-OJ Case Study)"
source_section: "O5"
tags: ["opinion", "system-design", "architecture", "queues", "isolation", "entropy-oj"]
draft: true
private: false
---

Aamir's system design approach:
- **Separate by latency and risk:** Web request handlers should never perform CPU-intensive or unbounded untrusted tasks. In Entropy-OJ, the API records the submission and enqueues it, while an asynchronous worker evaluates code under strict OS timeouts and resource limits.
- **State coordination:** Separate domain records (MongoDB) from ephemeral job state and queue coordination (Redis/BullMQ).
- **Service boundaries:** Decomposing systems across cloud environments (Render frontend/API, Azure worker/Redis) introduces network and connection boundaries that require explicit timeouts, keep-alives, and observability.

---
id: "opinion-what-makes-code-good"
type: "opinion"
title: "What Makes Code Good"
source_section: "O6"
tags: ["opinion", "code-quality", "software-engineering", "best-practices"]
draft: true
private: false
---

Aamir defines good code as:
- Correct, understandable, testable, maintainable, and secure for its threat model.
- Makes assumptions explicit and avoids unnecessary abstraction.
- Based on empirical measurements rather than speculative optimization or unverified claims.
- Conforms to clean conventions, provides informative diagnostics upon failure, and can be refactored without breaking unrelated behavior.

---
id: "opinion-ai-generated-code"
type: "opinion"
title: "Defensible Stance on AI-Generated Code"
source_section: "O7, A4"
tags: ["opinion", "ai-tools", "responsibility", "code-review", "engineering-standards"]
draft: true
private: false
---

Aamir's core stance: AI-generated code is not automatically good code.

While AI coding tools accelerate implementation, exploration, and test generation, the software engineer remains strictly responsible for correctness, security, edge-case coverage, and maintainability.

The critical metric in software engineering is not who typed the line of code, but whether the resulting system functions correctly, has been thoroughly verified with tests, and can be explained and maintained by the engineers who own it.

---
id: "opinion-ai-engineering-misconception"
type: "opinion"
title: "The Biggest Misconception About AI Engineering"
source_section: "O8"
tags: ["opinion", "ai-engineering", "llm", "rag", "production-ai"]
draft: true
private: false
---

The most common misconception about AI engineering is that it primarily consists of writing clever prompts or calling an LLM API.

In reality, a production-grade AI system requires data preparation, robust retrieval indexing, structured schema validation, failure recovery, adversarial guardrails, evaluation suites, cost/latency optimization, and safe UX degradation when the model is unavailable or inaccurate. The model itself is only one component within a broader software system.
