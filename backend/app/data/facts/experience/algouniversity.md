---
id: "exp-algouniversity-role"
type: "experience"
title: "AlgoUniversity Software Development Externship — Role Overview"
source_section: "X1, X2"
tags: ["algouniversity", "externship", "work-experience", "solo", "remote"]
draft: true
private: false
---

Aamir Mohammed Khan worked as a Software Development Extern at AlgoUniversity from July 2026 to August 2026 (two months). He obtained this role as part of the AlgoUniversity Accelerator Batch. The externship was fully remote, unpaid, and solo — every intern completed their own assignment independently, with mentorship available from AlgoUniversity mentors. Aamir's reporting role/title was Software Engineering Co-op Intern. Working hours were not formally defined or tracked.

The externship was associated with the Entropy-OJ project, which Aamir developed as his individual assignment. He had complete authorship over every design decision, component, and fix. The mentors were available for guidance and advice but were not co-authors of the implementation.

---
id: "exp-algouniversity-built"
type: "experience"
title: "AlgoUniversity Externship — What Was Built"
source_section: "X2, X6"
tags: ["entropy-oj", "fullstack", "mern", "redis", "ai-features", "algouniversity"]
draft: true
private: false
---

During the AlgoUniversity externship, Aamir built and deployed the full Entropy-OJ platform as a solo project. The outcome was a deployed fullstack application including a React/TypeScript frontend, Node.js/Express API, MongoDB database, Redis/BullMQ queues, a separate execution worker, Linux code-execution controls, and three AI workflows (Socratic Debug Copilot, QA Auditor, and complexity classifier).

Aamir personally authored the architecture, every component, and every fix. AlgoUniversity mentors provided guidance and advice but did not share implementation ownership.

---
id: "exp-algouniversity-cloud-arch"
type: "experience"
title: "AlgoUniversity Externship — Cloud Architecture"
source_section: "X6"
tags: ["cloud", "architecture", "vercel", "render", "azure", "mongodb-atlas", "redis", "deployment"]
draft: true
private: false
---

Aamir deployed the Entropy-OJ platform across multiple cloud services:

- **Frontend:** React/Vite application hosted on Vercel.
- **API/Application server:** Node.js/Express hosted on Render.
- **Database:** MongoDB Atlas for persistent data storage.
- **Queue/Broker and Worker:** Redis/BullMQ and the execution worker running on an Azure VM, with Docker-based deployment components documented in the README.
- **AI Providers:** Gemini Flash, Groq, and OpenRouter in a fallback design.

This separation keeps the UI, request handling, persistence, and CPU-bound code execution in different roles. The Redis connection crosses cloud/network boundaries (Render to Azure), which was significant during the queue-timeout debugging investigation. The setup can be described as separate deployed frontend/API/worker components with distinct service boundaries.

---
id: "exp-algouniversity-hardest-bug"
type: "experience"
title: "AlgoUniversity Externship — Hardest Bug (Redis ETIMEDOUT)"
source_section: "X7, X8"
tags: ["debugging", "redis", "distributed-systems", "networking", "tcp-keepalive", "azure"]
draft: true
private: false
---

The hardest technical problem Aamir encountered during the externship was an intermittent delay between a submission being saved and its execution job reaching the worker. The UI showed "running" while the worker appeared idle, so the symptom initially looked like a judge-worker or VM issue.

Aamir compared queue logs and timestamps, found a Redis `ETIMEDOUT` error, and identified a 2-minute-12-second gap between enqueue events. The root cause was the idle Redis connection timing out across the Render-to-Azure network boundary.

The fix involved configuring TCP keep-alive at 30-second intervals on the server-side Redis connection and increasing the Azure public-IP idle timeout to 30 minutes as an additional safeguard. After redeployment, a subsequent test appeared to process promptly.

Note on unverified metrics: Aamir did NOT measure or claim a 35% API latency reduction. The measured improvement was resolving the 2-minute-12-second Redis ETIMEDOUT connection delay. Do not claim "35% faster".

The lesson learned: "My first instinct was to investigate the worker and VM because that was where execution happened. The worker was actually idle, so that explanation did not fit all the evidence. I compared logs and timing across the queue boundary, found a Redis timeout, and applied a targeted connection-level fix. I learned not to diagnose a distributed-system issue from the visible symptom alone; I should trace the request path and test assumptions before changing more components."

---
id: "exp-algouniversity-mentor-feedback"
type: "experience"
title: "AlgoUniversity Externship — Mentor Feedback"
source_section: "X9"
tags: ["feedback", "mentorship", "algouniversity", "entropy-oj"]
draft: true
private: false
---

Aamir received detailed feedback from two mentors at AlgoUniversity. Both appreciated the overall technical implementation, creative gamified UI/UX, backend architecture, and ambitious AI integrations. They particularly highlighted the Galaxy Node Map and the combination of MERN stack, Redis, BullMQ, and Docker-based sandboxing as strong aspects of the project.

Their primary recommendations included:

- Improve Docker sandbox execution stability by investigating potential Azure infrastructure issues, particularly CPU credit exhaustion and resource limitations, before considering a cloud provider migration.
- Enhance the watchdog mechanism to capture system metrics during failures for better debugging.
- Make the AI-powered features more visible and accessible within the user interface.

Overall, the feedback was encouraging, with specific, actionable suggestions for improving infrastructure reliability, debugging capabilities, and user experience.

---
id: "exp-algouniversity-improvements"
type: "experience"
title: "AlgoUniversity Externship — What Would Change"
source_section: "X10"
tags: ["retrospective", "improvements", "testing", "observability", "algouniversity"]
draft: true
private: false
---

If Aamir were to redo or continue the Entropy-OJ project, he would focus on making verification more systematic:

- Add a repeatable test for the idle-connection case to reproduce the Redis ETIMEDOUT scenario.
- Measure enqueue latency before and after any fix to quantify improvements.
- Run the full relevant test suite after changes.
- Add queue delay/error observability and monitoring dashboards.
- Document an operational checklist for deployment and troubleshooting.
- Expand sandbox threat-model testing with specific malicious-input and escape scenarios.
- Reconsider whether stronger isolation (e.g., container/VM boundary) is appropriate for the threat model.

These are proposed future improvements, not claims of work already completed.

---
id: "exp-algouniversity-concurrency"
type: "experience"
title: "AlgoUniversity Externship — Concurrency Limits and Load Testing"
source_section: "X4, J7"
tags: ["entropy-oj", "concurrency", "load-testing", "worker-concurrency", "bullmq", "redis", "limits", "throughput"]
draft: true
private: false
---

In Entropy-OJ, Redis and BullMQ are used to decouple long-running judge executions from the HTTP request path. Worker concurrency is configured to 2 in the BullMQ settings, and the worker uses process semaphores, active-process tracking, lock renewal, and stale-job recovery.

Actual maximum concurrent submissions tested: formal high-concurrency load testing and throughput benchmarks have not been completed. Do not claim high concurrency without degradation or load-test results without evidence. Configured worker concurrency (2) is a configuration limit, not a proven load-test benchmark.
