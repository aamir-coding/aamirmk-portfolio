---
id: "proj-ai-assistant-overview"
type: "project"
title: "AI Digital Assistant Portfolio — Overview"
source_section: "Résumé: Technical Projects; J1, J2 (Project D)"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "portfolio", "rag", "chatbot", "recruiter", "fastapi", "react"]
draft: true
private: false
---

The AI Digital Assistant Portfolio is Aamir's completed and shipped recruiter chatbot. It uses retrieval-augmented generation (RAG) over a curated knowledge base to answer questions about his education, engineering experience, projects, skills, and interests.

Recruiters can explore his background through streamed, cited answers and interactive project cards, or paste a job description to get a structured fit report with evidence and skill gaps. The assistant can abstain when its sources do not support an answer.

This is Aamir's portfolio project, developed with help from AI coding agents (Claude/Claude Code, GitHub Copilot, ChatGPT, Gemini, and Antigravity). Aamir sets requirements, steers implementation, reviews generated changes, debugs integrations, and verifies actual behaviour. The AI assistance accelerates the workflow; it does not transfer responsibility for correctness or security to the tools.

---
id: "proj-ai-assistant-architecture"
type: "project"
title: "AI Digital Assistant Portfolio — Architecture and Stack"
source_section: "Résumé: Technical Projects; J4, J5 (Project D)"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "fastapi", "react", "typescript", "rag", "sse", "hybrid-retrieval", "bm25", "embeddings"]
draft: true
private: false
---

The shipped system includes:

- **Backend:** FastAPI (Python), Pydantic v2, and the Groq API for LLM inference.
- **Frontend:** React 19 with TypeScript and Vite.
- **Retrieval:** Hybrid BM25 and precomputed FastEmbed ONNX embeddings over curated Markdown and YAML chunks. Reciprocal Rank Fusion (RRF) combines lexical and semantic ranks.
- **Streaming:** Starlette `StreamingResponse` sends server-sent events (SSE) over POST for answer tokens, citations, and project cards.
- **Tool calling:** The LLM can call `show_project_card`. The backend validates the arguments and returns a card from the server-owned project catalog.
- **Persistence:** Supabase PostgreSQL with SQLAlchemy 2.0, connection pooling, and Alembic migrations for recruiter handoffs, analytics, and shared summaries.
- **Job-description fit:** A five-stage pipeline extracts requirements, retrieves evidence, judges alignment, calculates the score, and summarizes strengths and gaps.

The portfolio UI posts a recruiter's question to FastAPI. The backend retrieves relevant chunks and passes them to the LLM as context. Visitors can follow citations back to the source material, inspect project cards, and use the consent-based recruiter handoff.

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

1. **Why Aamir chose RAG:** Recruiter answers need current, citable facts about Aamir's work. Retrieval-augmented generation grounds answers in relevant chunks from the curated knowledge base. Aamir can update his profile and project details, then rebuild the search index without retraining the LLM. The trade-off is that retrieval can miss relevant evidence or select noisy chunks.

2. **Hybrid retrieval (BM25 plus embeddings):** Lexical search helps with exact technologies and project names, while embeddings can find semantically related questions. The trade-off is added indexing, fusion, and tuning complexity.

3. **Citations and an abstention/handoff path:** Citations support verification of claims, and abstention is safer than guessing when the knowledge base cannot support an answer. Quality depends on correct source metadata and links from answers to retrieved chunks.

4. **AI-assisted development:** Agents accelerate coding, but generated code must be reviewed, run, tested, and understood. Aamir remains responsible for the behaviour and claims of the shipped system.

5. **Release verification:** Before publishing, check retrieval scores, verify that citations resolve, and replay cases that exercise abstention, rate limiting, and safety controls. End-to-end checks also cover streamed chat, project cards, and job-description fit reports.

---
id: "proj-ai-assistant-status"
type: "project"
title: "AI Digital Assistant Portfolio — Current Status"
source_section: "Résumé: Technical Projects; portfolio release record"
source_url: "https://github.com/aamir-coding/aamirmk-portfolio"
tags: ["ai-assistant", "status", "shipped", "deployment", "knowledge-base"]
draft: true
private: false
---

The AI Digital Assistant Portfolio is complete and shipped. The React 19 frontend is deployed on Vercel and the FastAPI backend on Render. Recruiters can open the public app without logging in.

The release includes cited chat over Starlette SSE, hybrid BM25 and FastEmbed ONNX retrieval, tool-called project cards, the Supabase PostgreSQL data layer, and a job-description fit report workflow.

Automated checks cover retrieval and recorded chat and fit workflows. These checks measure retrieval and replay behavior. Independent generation accuracy has not been established.

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
