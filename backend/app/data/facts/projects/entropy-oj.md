---
id: "proj-entropy-oj-pitch"
type: "project"
title: "Entropy Online Judge — Pitch and Problem"
source_section: "J1, J2 (Project A)"
tags: ["entropy-oj", "online-judge", "dsa", "competitive-programming", "ai-features"]
draft: true
private: false
---

Entropy-OJ is a competitive-programming and DSA learning platform that compiles and evaluates C++17 and Python 3.11 submissions in a controlled Linux execution environment and adds AI-powered debugging, problem auditing, and complexity classification.

It helps learners practise data structures and algorithms, submit code, inspect verdicts and compiler/runtime diagnostics, review previous submissions, and get progressive AI hints without being handed a full solution. It also helps problem setters audit problem statements, examples, and judge packages.

The project was developed as Aamir Mohammed Khan's individual assignment during his AlgoUniversity Software Development Externship (July–August 2026). It was a solo project with complete authorship by Aamir. Mentors were available for guidance but did not share implementation ownership.

---
id: "proj-entropy-oj-stack"
type: "project"
title: "Entropy Online Judge — Technologies, Stack and Architecture"
source_section: "J4, J5 (Project A)"
tags: ["entropy-oj", "technologies", "tech-stack", "react", "typescript", "nodejs", "express", "mongodb", "redis", "bullmq", "azure", "architecture"]
draft: true
private: false
---

**Technologies and Tech Stack:**

- React 19, TypeScript, and Vite for an interactive responsive coding workspace.
- Monaco Editor for in-browser code editing.
- Node.js and Express for API endpoints and application logic.
- MongoDB Atlas for users, problems, test cases, submissions, and solution records.
- Redis and BullMQ for asynchronous judging and background AI classification.
- C++17/GCC and Python 3.11 as supported execution languages.
- Linux process controls and a separate worker for code execution.
- Gemini Flash, Groq, and OpenRouter for AI workflows with provider fallback.
- Deployed across Vercel (frontend), Render (API), MongoDB Atlas (database), and an Azure VM (worker/Redis).

**Architecture:** The React client sends authenticated requests to the Express API. The API stores submission metadata in MongoDB and queues full judge work through BullMQ/Redis instead of waiting for execution inside the HTTP request. A separate worker retrieves the job and runs test cases through a Linux runner script with time and resource limits, then persists verdict and runtime/memory information. The client polls for the result and displays diagnostics and submission history. Separate AI endpoints provide progressive hints, problem-package audits, and post-acceptance classification.

---
id: "proj-entropy-oj-design"
type: "project"
title: "Entropy Online Judge — Design Decisions"
source_section: "J6 (Project A)"
tags: ["entropy-oj", "design-decisions", "async-queue", "sandboxing", "ai-fallback", "security"]
draft: true
private: false
---

Key design decisions and trade-offs in Entropy-OJ:

1. **Asynchronous queue and dedicated worker:** Long-running code execution is separated from request handling via BullMQ/Redis, allowing the API to return immediately while the worker processes jobs. Trade-off: introduces queue/worker operational complexity and requires result polling.

2. **Direct process sandboxing with OS limits:** Avoids per-test container startup overhead and simplifies the worker path. Trade-off: the isolation provided is not equivalent to a hardened container/VM boundary for every threat model.

3. **Provider fallback and structured-output repair:** The AI workflow can fall back between Gemini Flash, Groq, and OpenRouter, improving resilience to provider failures and malformed responses. Trade-off: adds branches, testing needs, latency/cost trade-offs, and configuration complexity.

4. **Do not send hidden judge cases to AI hints:** The Socratic Debug Copilot receives only public sample cases and the student's code, reducing leakage risk. A code-block-stripping guard removes corrected snippets from hint output. Trade-off: depends on correct prompt boundaries and adequate tests; these are designed safeguards, not fully proven guarantees.

---
id: "proj-entropy-oj-ai-features"
type: "project"
title: "Entropy Online Judge — Three AI Features"
source_section: "J4, J5, J6, X5 (Project A)"
tags: ["entropy-oj", "ai", "socratic-debug", "qa-auditor", "complexity-classifier", "llm"]
draft: true
private: false
---

Entropy-OJ includes three AI-powered workflows:

1. **Socratic Debug Copilot:** Provides progressive debugging hints to learners without giving away the full solution. It receives only the student's code and public sample test cases — hidden judge cases are excluded from the prompt. A code-block-stripping guard removes corrected code snippets from the output, so learners get guidance rather than answers. These are designed safeguards; full negative testing to confirm hidden tests never enter prompts is deferred.

2. **QA Auditor:** Audits problem statements, examples, and judge packages for problem setters, helping identify inconsistencies or issues in problem content.

3. **Complexity Classifier:** A background AI classification workflow that runs post-acceptance to categorise solution complexity.

All three features use a provider fallback design across Gemini Flash, Groq, and OpenRouter. Structured output repair is applied when providers return malformed responses.

---
id: "proj-entropy-oj-security"
type: "project"
title: "Entropy Online Judge — Code Execution Security"
source_section: "X3, J12 Q2 (Project A)"
tags: ["entropy-oj", "security", "sandboxing", "linux", "ulimit", "code-execution"]
draft: true
private: false
---

Entropy-OJ executes untrusted user code through a Linux `runner_process.sh` script and direct child processes under a dedicated unprivileged user. Documented controls include:

- Wall-clock timeouts to prevent long-running submissions.
- Linux `ulimit` restrictions on process creation and file output.
- Capped stdout/stderr to prevent output flooding.
- Per-job workspaces with cleanup after execution.
- GNU `time`-based peak-memory measurement.
- Child-process tracking and termination handling.
- API access controls that protect users' own submission records.
- Payload validation on API inputs.

The design uses direct process sandboxing, which reduces container-startup overhead but is not equivalent to a hardened container/VM boundary for every threat model. These are documented safeguards, not proof that the system is perfectly secure. Exact malicious-input and attack tests actually run are deferred for future work. Aamir has stated he would keep testing the threat model and assess stronger isolation options.

---
id: "proj-entropy-oj-debug-story"
type: "project"
title: "Entropy Online Judge — Redis ETIMEDOUT Debug Story"
source_section: "J8, J12 Q3 (Project A)"
tags: ["entropy-oj", "debugging", "redis", "etimedout", "distributed-systems", "tcp-keepalive"]
draft: true
private: false
---

The hardest bug in Entropy-OJ was an intermittent submission delay: the UI showed "running" while the execution worker remained idle. Comparing enqueue logs and timestamps revealed a Redis `ETIMEDOUT` error and a 2-minute-12-second gap between relevant enqueue events.

The investigation process: Aamir compared the API enqueue logs with worker behaviour at different times. The worker was idle until the job arrived, and the relevant enqueue events were separated by the 2m12s gap with a Redis connection timeout. This shifted the investigation from compiler speed or VM issues to the server-to-Redis network connection (which crosses cloud boundaries from Render to Azure).

The fix: Aamir configured TCP keep-alive at 30-second intervals on the server-side Redis connection and increased the Azure public-IP idle timeout to 30 minutes as an additional safeguard. A subsequent test appeared to process promptly. This is a practical debugging example involving logs, timing analysis, networking, and asynchronous job flow across cloud boundaries.

Note on unverified metrics: Aamir did NOT measure or claim a 35% API latency reduction. The verified bug fix resolved the 2m12s Redis ETIMEDOUT connection delay. Do not claim "35% faster".

---
id: "proj-entropy-oj-interview-qa"
type: "project"
title: "Entropy Online Judge — Interview Q&A"
source_section: "J12 (Project A)"
tags: ["entropy-oj", "interview", "questions", "queue", "security", "debugging"]
draft: true
private: false
---

**Q: Why use a queue for code execution?**
Code execution can take longer than a normal web request and may hang or exhaust resources. A queue lets the API record the submission and return a submission ID while a separate worker processes it. This improves separation and recovery, but introduces asynchronous state, retries, polling, and observability requirements.

**Q: How do you reduce risks when running untrusted code?**
The documented runner uses an unprivileged user, timeouts and OS resource limits, output caps, per-job workspaces, and process tracking/cleanup. API access controls also protect users' submission records. These controls reduce risk but do not prove perfect isolation; Aamir would keep testing the threat model and assess stronger isolation options.

**Q: How did you debug the submission delay?**
Aamir compared the API enqueue logs with worker behaviour at different times. The worker was idle until the job arrived, and the relevant enqueue events were 2 minutes and 12 seconds apart with a Redis `ETIMEDOUT` error. That shifted the investigation from compiler speed to the server-to-Redis connection. He configured TCP keep-alive, increased the network idle timeout as a fallback, and observed prompt processing in a subsequent test.

---
id: "proj-entropy-oj-links"
type: "project"
title: "Entropy Online Judge — Links and Status"
source_section: "J10, J11 (Project A)"
tags: ["entropy-oj", "links", "live-app", "demo"]
draft: true
private: false
---

**Links:**

- Live app: https://entropy-oj.vercel.app
- Repository: https://github.com/aamir-coding/Entropy-OJ
- Demo video (complete technical walkthrough): https://www.loom.com/share/a982d7d46b654d11a39dd5e39f2372de
- Architecture diagram: a Mermaid architecture diagram exists in the repository README, showing the client, application/AI layer, external providers, Redis/BullMQ queues, execution worker, and data layer.

**Current status:** The application is deployed across Vercel, Render, MongoDB Atlas, and an Azure VM. The app is live and available. Users can create a new account within a minute. For admin panel login, contact Aamir. Potential issues could arise from massive user overload due to Render's free tier limitations and Azure VM resource limits.

All apps were confirmed working as of 01 November 2026.
