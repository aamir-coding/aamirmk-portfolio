---
id: "proj-ai-assistant-overview"
type: "project"
title: "AI Digital Assistant Portfolio — Overview"
source_section: "J1, J2 (Project D)"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "portfolio", "rag", "chatbot", "recruiter", "fastapi", "react"]
draft: true
private: false
---

The AI Digital Assistant Portfolio is a RAG-based recruiter chatbot — an AI portfolio assistant intended to answer recruiter questions about Aamir's education, engineering experience, projects, skills, and interests using a curated knowledge base and retrieval-augmented generation.

Recruiters may have limited time to read a resume or navigate multiple links. The assistant is designed to make verified information about Aamir's background easy to explore conversationally, answer technical project questions with evidence, and avoid inventing information missing from the approved knowledge base.

This is Aamir's portfolio project, developed with help from AI coding agents (Claude/Claude Code, GitHub Copilot, ChatGPT, Gemini, and Antigravity). Aamir sets requirements, steers implementation, reviews generated changes, debugs integrations, and verifies actual behaviour. The AI assistance accelerates the workflow; it does not transfer responsibility for correctness or security to the tools.

---
id: "proj-ai-assistant-architecture"
type: "project"
title: "AI Digital Assistant Portfolio — Architecture and Stack"
source_section: "J4, J5 (Project D)"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "fastapi", "react", "typescript", "rag", "sse", "hybrid-retrieval", "bm25", "embeddings"]
draft: true
private: false
---

The intended and documented stack includes:

- **Backend:** FastAPI (Python) with Pydantic v2.
- **Frontend:** React with TypeScript and Vite.
- **Retrieval:** Hybrid retrieval combining BM25 (lexical) and ONNX embeddings (semantic), with curated Markdown/YAML knowledge-base files.
- **Streaming:** Server-sent events (SSE) for real-time response streaming.
- **LLM:** Groq API with provider configuration.
- **Features:** Source citations, structured tool calling, and a human/contact handoff path.

**Architecture:** The portfolio UI sends a recruiter's question to a backend API. The backend retrieves relevant approved knowledge-base chunks using a hybrid retrieval pipeline, then passes grounded context to an LLM to generate a response. The response identifies the source evidence so a visitor can trace claims back to approved profile and project material. Streaming and a human/contact handoff are part of the intended user experience.

---
id: "proj-ai-assistant-design"
type: "project"
title: "AI Digital Assistant Portfolio — Design Decisions"
source_section: "J6 (Project D)"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "design-decisions", "rag", "hybrid-retrieval", "citations", "ai-development"]
draft: true
private: false
---

Key design decisions for the AI Digital Assistant Portfolio:

1. **RAG instead of relying on model memory:** Answers are grounded in approved information and can be updated without retraining. Aamir's profile and project details change, and RAG lets him update source documents, retrieve evidence, and generate answers using relevant chunks. Trade-off: retrieval can miss relevant evidence or select noisy chunks.

2. **Hybrid retrieval (BM25 plus embeddings):** Lexical search helps with exact technologies and project names, while embeddings can find semantically related questions. Trade-off: adds indexing, fusion, and tuning complexity.

3. **Citations and an abstention/handoff path:** Citations support verification of claims, and abstention is safer than guessing when the knowledge base cannot support an answer. Quality depends on correct source metadata and links from answers to retrieved chunks.

4. **AI-assisted development:** Agents accelerate coding, but generated code must be reviewed, run, tested, and understood. Aamir remains responsible for the behaviour and claims of the shipped system.

---
id: "proj-ai-assistant-status"
type: "project"
title: "AI Digital Assistant Portfolio — Current Status"
source_section: "J11, V2, V7 (Project D)"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "status", "development", "knowledge-base"]
draft: true
private: false
---

The AI Digital Assistant Portfolio is under active development. It has a live deployment URL and a repository URL. The knowledge-base and RAG content is currently being prepared through a structured questionnaire process.

No login is required to use the application. No verified retrieval-quality, answer-quality, latency, cost, or evaluation results are available yet. The system should not be described as complete until it has passed end-to-end verification.

Current development is ongoing as of November 2026.

---
id: "proj-ai-assistant-links"
type: "project"
title: "AI Digital Assistant Portfolio — Links"
source_section: "J10, V1 (Project D)"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "links", "repository", "live-app"]
draft: true
private: false
---

- Live app: https://aamirmk-portfolio.vercel.app
- Repository: https://github.com/aamir-coding/aamirmk-portfolio
