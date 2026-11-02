"""Authoritative catalog of Aamir's projects grounded in verified facts.

Design Principle 2: "The model selects, your server supplies. Cards and facts
come from your data files, never from generated text, so the UI cannot
hallucinate a project."
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProjectCardData(BaseModel):
    """Authoritative project schema supplied by the server when summoned."""

    id: str = Field(description="Unique project identifier, e.g. 'entropy-oj'")
    title: str = Field(description="Project title")
    subtitle: str = Field(description="Short descriptive subtitle/pitch")
    summary: str = Field(description="Executive summary of the project")
    role: str = Field(
        default="Solo Author / Lead Developer",
        description="Aamir's role on the project",
    )
    tech_stack: list[str] = Field(description="Core technologies used")
    highlights: list[str] = Field(
        description="Key technical feats and architectural highlights"
    )
    metrics: dict[str, str] = Field(
        default_factory=dict,
        description="Key project metrics, e.g. test counts, response times",
    )
    github_url: str | None = Field(
        default=None,
        description="GitHub repository URL",
    )
    live_url: str | None = Field(
        default=None,
        description="Live deployment URL",
    )
    source_sections: list[str] = Field(
        default_factory=list,
        description="Verified questionnaire/resume receipts",
    )
    architecture_details: str = Field(
        description="Deep architectural breakdown and trade-offs for modal inspection"
    )

    model_config = ConfigDict(frozen=True)


PROJECT_CATALOG: dict[str, ProjectCardData] = {
    "entropy-oj": ProjectCardData(
        id="entropy-oj",
        title="Entropy Online Judge",
        subtitle="Competitive Programming & DSA Platform with Socratic AI Debugging",
        summary=(
            "A competitive-programming platform that compiles and evaluates "
            "C++17 and Python 3.11 submissions in an isolated Linux environment, "
            "featuring progressive AI debugging hints and problem auditing."
        ),
        role="Solo Author (AlgoUniversity Externship)",
        tech_stack=[
            "React 19",
            "TypeScript",
            "Node.js",
            "Express",
            "MongoDB Atlas",
            "Redis",
            "BullMQ",
            "C++17 / GCC",
            "Linux Runner",
            "Azure VM",
            "Groq",
        ],
        highlights=[
            (
                "Asynchronous execution queue: BullMQ and Redis decouple code "
                "judging from HTTP handling, offloading jobs to a dedicated worker."
            ),
            (
                "Socratic Hint Engine: Passes only public sample cases and student "
                "code to LLM, stripping full solutions and protecting hidden suites."
            ),
            (
                "Provider fallback: Resilient workflow switching across Gemini Flash, "
                "Groq, and OpenRouter with structured JSON output repair."
            ),
            (
                "Monaco Editor integration for in-browser IDE experience with "
                "real-time compilation and runtime diagnostics."
            ),
        ],
        metrics={
            "Worker Model": "Decoupled Redis/BullMQ",
            "Supported Languages": "C++17 (GCC), Python 3.11",
            "Sandboxing": "Linux OS Limits & Dedicated VM",
            "Deployment": "Vercel + Render + Azure VM",
        },
        github_url="https://github.com/aamir-coding/entropy-oj",
        live_url="https://entropy-oj.vercel.app",
        source_sections=["J1", "J2", "J4", "J5", "J6"],
        architecture_details="""### System Architecture
The React client connects to an Express API deployed on Render.
Submissions are persisted in MongoDB Atlas and pushed to a BullMQ queue
backed by Redis on an Azure VM.

```
[React 19] ──HTTP──► [Express API] ──Enqueue──► [Redis / BullMQ]
                                                       │
                                                  Worker Pull
                                                       ▼
[MongoDB Atlas] ◄──Persist Result── [Linux Sandbox Runner (GCC/Python)]
```

### Key Architectural Decisions & Trade-offs
1. **Asynchronous Queue over HTTP Blocking:** Judging untrusted code
   can take seconds. BullMQ worker execution ensures API endpoints
   respond in <50ms with a submission ticket.
2. **Linux Process Controls:** Sandboxed execution via process limits
   (RLIMIT_CPU, RLIMIT_AS) prevents denial of service while avoiding
   container spin-up overhead.
3. **Socratic Guardrails:** AI endpoints only inspect public sample
   cases to prevent test leakage.""",
    ),
    "ai-digital-assistant": ProjectCardData(
        id="ai-digital-assistant",
        title="AI Digital Assistant Portfolio",
        subtitle="Grounded Recruiter Agent with Hybrid RAG & Generative Dossier UI",
        summary=(
            "A production-grade, zero-hallucination portfolio system where "
            "recruiters chat with an AI assistant grounded strictly in "
            "verified facts about Aamir, featuring hybrid retrieval, SSE "
            "streaming, and server-supplied UI cards."
        ),
        role="Solo Author & Architect",
        tech_stack=[
            "Python 3.13",
            "FastAPI",
            "React",
            "TypeScript",
            "BM25",
            "FastEmbed ONNX",
            "Reciprocal Rank Fusion",
            "SSE over POST",
            "Groq API",
            "Vite",
        ],
        highlights=[
            (
                "In-process hybrid retrieval: Custom Okapi BM25 combined with "
                "BAAI/bge-small-en-v1.5 embeddings using Reciprocal Rank Fusion."
            ),
            (
                "Passed 512MB RAM Gate: Total container footprint is 227MB with "
                "sub-10ms retrieval latency running completely on CPU."
            ),
            (
                "Server-Supplied Generative UI: Model triggers function calls; backend "
                "supplies immutable verified schemas to guarantee zero hallucination."
            ),
            (
                "Deterministic Safety Seams: Pre-call regex guardrails block "
                "injections at 0 token cost; sliding-window rate limiter "
                "prevents abuse."
            ),
        ],
        metrics={
            "Retrieval Hit Rate@5": "100.0% (45/45 queries)",
            "Mean Reciprocal Rank": "0.8778 MRR",
            "CPU Retrieval Latency": "9.39 ms average",
            "Container Footprint": "227 MB (<50% of 512MB limit)",
        },
        github_url="https://github.com/aamir-coding/aamirmk-portfolio",
        live_url="https://aamirmk-portfolio.vercel.app",
        source_sections=["J1", "J2", "J4", "J5", "J6"],
        architecture_details="""### System Architecture
The application separates conversational intelligence from data authority:

```
[React Dossier UI] ──SSE over POST──► [FastAPI Application]
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
         [In-Process Hybrid RAG]                              [Deterministic Safety]
         - Okapi BM25 (lexical)                              - Pre-call regex guards
         - FastEmbed ONNX (semantic)                         - Sliding window limiter
         - Reciprocal Rank Fusion (k=60)                     - UTC daily quota guard
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              ▼
                                     [LLM Seam / Groq]
                                              │ (show_project_card)
                                              ▼
                              [Authoritative Project Catalog]
```

### Key Architectural Decisions
1. **Hybrid Fusion over Vector-Only:** Dense vectors alone struggle with
   exact technical tokens (e.g. 'ETIMEDOUT', 'BullMQ'); BM25 provides
   exact keyword precision.
2. **Protocol Seams:** LLM and Retriever live behind abstract protocols
   (`LLMClient`, `Retriever`), enabling sub-second unit tests in CI
   with zero API cost.""",
    ),
    "health-premium-predictor": ProjectCardData(
        id="health-premium-predictor",
        title="Health Premium Predictor",
        subtitle="Machine Learning Health Insurance Regression Web App",
        summary=(
            "An educational machine learning web application that estimates health "
            "insurance premiums using an XGBoost regression model and an interactive "
            "Streamlit interface."
        ),
        role="Solo Author",
        tech_stack=[
            "Python",
            "XGBoost",
            "Scikit-Learn",
            "Streamlit",
            "Pandas",
            "NumPy",
        ],
        highlights=[
            (
                "End-to-end regression pipeline mapping demographic, lifestyle, and "
                "health risk factors into estimated premium costs."
            ),
            (
                "Reported evaluation metrics: R² score of 0.99 and approximately 3% "
                "prediction error on evaluated dataset."
            ),
            (
                "Transparent documentation: clearly framed as an educational ML tool "
                "rather than insurance-grade financial advice."
            ),
        ],
        metrics={
            "Reported R²": "0.99",
            "Reported Error": "~3%",
            "UI Framework": "Streamlit",
            "Status": "Live on Cloud",
        },
        github_url="https://github.com/aamir-coding/health-prem-predict",
        live_url="https://health-prem-prediction.streamlit.app/",
        source_sections=["J1", "J2", "J3", "J7", "J10", "J14"],
        architecture_details="""### ML Pipeline & Workflow
User submits lifestyle parameters (BMI, smoking status, age, region).
The feature vector is transformed using a scikit-learn preprocessing
pipeline and scored against a trained XGBoost regression model.

```
[Streamlit UI] ──► [Scikit Preprocessing] ──► [XGBoost] ──► [Estimate]
```

### Verification & Defensibility
- Reported R² of 0.99 on the test partition.
- Documented in the knowledge base as an educational project
  demonstrating tabular regression, feature encoding, and deployment.""",
    ),
    "health-tracker": ProjectCardData(
        id="health-tracker",
        title="HealthTracker",
        subtitle="Full-Stack Progressive Web App for Health Analytics",
        summary=(
            "A full-stack health-tracking application with a Progressive "
            "Web App (PWA) experience, responsive health metric charts, "
            "and automated GitHub Actions CI."
        ),
        role="Solo Author",
        tech_stack=[
            "React",
            "TypeScript",
            "PWA",
            "MongoDB Atlas",
            "Node.js",
            "Express",
            "GitHub Actions CI",
        ],
        highlights=[
            (
                "Progressive Web App with responsive data views, service worker "
                "caching, and app-like installability."
            ),
            (
                "Automated GitHub Actions CI verifying build integrity and test "
                "execution on every commit."
            ),
            (
                "Full persistence via MongoDB Atlas with demo accounts provided "
                "directly on login view."
            ),
        ],
        metrics={
            "Architecture": "PWA + Express API",
            "Database": "MongoDB Atlas",
            "CI/CD": "GitHub Actions",
            "Status": "Live on Vercel/Render",
        },
        github_url="https://github.com/aamir-coding/health-tracker",
        live_url="https://health-tracker-alpha-one.vercel.app",
        source_sections=["J1", "J2", "J3", "J10", "J11"],
        architecture_details="""### Architecture
A responsive React Progressive Web App communicating with an Express
backend on Render. Data is persisted in MongoDB Atlas with compound
indexes for efficient daily metric lookups.""",
    ),
    "keynone": ProjectCardData(
        id="keynone",
        title="Keynone",
        subtitle="Local Private Voice Dictation for Windows",
        summary=(
            "An open-source, 100% offline speech-to-text dictation application for "
            "Windows that removes filler words, self-corrects on the fly, and formats "
            "punctuation at the cursor without cloud round-trips."
        ),
        role="Solo Author",
        tech_stack=[
            "Python",
            "Local Speech Models",
            "Windows OS APIs",
            "CPU Inference",
        ],
        highlights=[
            (
                "Zero cloud telemetry: Audio recording, transcription, and "
                "formatting run entirely on the local CPU."
            ),
            (
                "Smart speech cleanup: Automatically strips verbal pauses "
                "('um', 'uh', repetitions) and normalizes punctuation."
            ),
            (
                "Universal insertion: Sends keystrokes directly to the active "
                "cursor in any Windows desktop application."
            ),
        ],
        metrics={
            "Privacy": "100% Offline / Local",
            "Host OS": "Windows",
            "Execution": "CPU Inference",
            "Telemetry": "Zero Cloud Calls",
        },
        github_url="https://github.com/aamir-coding/keynone",
        live_url=None,
        source_sections=["X11", "V6"],
        architecture_details="""### Architecture
Keynone captures system audio through a push-to-talk hotkey, performs
on-device transcription with lightweight models, applies regex and
linguistic cleanup heuristics, and synthesizes keypress events to paste
the finalized text into the focused application.""",
    ),
    "vayusetu": ProjectCardData(
        id="vayusetu",
        title="VayuSetu",
        subtitle="Google Cloud Hackathon Award-Winning Clean Air & Logistics Platform",
        summary=(
            "A cloud-backed clean air and emergency logistics solution "
            "awarded 2nd Runner-Up in Google Cloud's 'Build with AI: "
            "Code for Communities' hackathon (Track 2: CleanAir & Clear Streets)."
        ),
        role="Core Collaborator (Team Pentium Connoisseurs, 4 members)",
        tech_stack=[
            "Google Cloud Platform",
            "AI APIs",
            "Python",
            "Geospatial Data",
        ],
        highlights=[
            (
                "Awarded 2nd Runner-Up in Google Cloud Track 2 "
                "('CleanAir & Clear Streets') among hundreds of national participants."
            ),
            (
                "Prototyped clean air corridor planning and delivery logistics using "
                "Google Cloud infrastructure."
            ),
            (
                "Verified receipt: Congratulatory email and authenticated "
                "Hack2Skill registration."
            ),
        ],
        metrics={
            "Award": "2nd Runner-Up",
            "Organizer": "Google Cloud & Hack2Skill",
            "Track": "CleanAir & Clear Streets",
            "Team Size": "4 Developers",
        },
        github_url=None,
        live_url="https://hack2skill.com/event/codeforcommunities2",
        source_sections=["X11", "AC3"],
        architecture_details="""### Project Context
VayuSetu was built during the Google Cloud 'Build with AI: Code for
Communities' hackathon (Aug–Sep 2026). Team Pentium Connoisseurs
engineered route planning algorithms optimizing for clean air pathways.""",
    ),
    "browser-games": ProjectCardData(
        id="browser-games",
        title="Interactive Browser Games",
        subtitle="2D Canvas Platformer & Memory Game Prototypes",
        summary=(
            "Creative coding exercises exploring client-side game loops, "
            "Canvas 2D rendering, collision detection, and parallax "
            "camera effects built from scratch."
        ),
        role="Solo Author",
        tech_stack=[
            "JavaScript",
            "HTML5 Canvas",
            "Web Audio API",
            "CSS3",
        ],
        highlights=[
            (
                "Hand-crafted 60fps update/render game loop without external game "
                "engine dependencies."
            ),
            (
                "Client-side physics, custom collision handling, and parallax "
                "camera tracking."
            ),
            "Sound synthesis and animated state machines for player feedback.",
        ],
        metrics={
            "Engine": "Pure Canvas 2D",
            "Framerate": "60 FPS Target",
            "Dependencies": "0 (Vanilla JS)",
        },
        github_url=None,
        live_url=None,
        source_sections=["J1", "J2", "J3", "J4", "J11"],
        architecture_details="""### Technical Design
Engineered around a `requestAnimationFrame` render loop separating state
mutation from screen drawing. Demonstrates fundamental computer science
concepts: frame delta calculations, axis-aligned bounding box (AABB)
collision checks, and sprite animation.""",
    ),
    "secure-auction": ProjectCardData(
        id="secure-auction",
        title="Secure Online Auction System",
        subtitle="Role-Based Auction Platform with Cryptographic Controls",
        summary=(
            "A security-focused learning project implementing role-based access "
            "control, Argon2 password hashing, and protected bidding transaction "
            "workflows in Django."
        ),
        role="Developer (Learning Project)",
        tech_stack=[
            "Python",
            "Django",
            "PostgreSQL",
            "Argon2",
            "RBAC",
        ],
        highlights=[
            (
                "Strict role-based access control (RBAC) protecting seller, bidder, "
                "and admin permission boundaries."
            ),
            (
                "Cryptographic password hashing using Argon2 and email verification "
                "on account registration."
            ),
            (
                "Honest reporting: documented as an educational prototype rather "
                "than a live financial exchange."
            ),
        ],
        metrics={
            "Security": "Argon2 + RBAC",
            "Database": "PostgreSQL",
            "Architecture": "Server-rendered Django",
        },
        github_url=None,
        live_url=None,
        source_sections=["J1", "J2", "J3", "J4", "J10"],
        architecture_details="""### Architecture
Built with Django's Model-View-Template pattern, enforcing atomic database
transactions during bidding rounds to prevent race conditions on auction
item increments.""",
    ),
}

PROJECT_ALIASES: dict[str, str] = {
    "entropy": "entropy-oj",
    "entropy_oj": "entropy-oj",
    "online-judge": "entropy-oj",
    "ai-assistant": "ai-digital-assistant",
    "portfolio": "ai-digital-assistant",
    "digital-assistant": "ai-digital-assistant",
    "health-premium": "health-premium-predictor",
    "insurance": "health-premium-predictor",
    "health-predictor": "health-premium-predictor",
    "healthtracker": "health-tracker",
    "health_tracker": "health-tracker",
    "key-none": "keynone",
    "vayu-setu": "vayusetu",
    "games": "browser-games",
    "auction": "secure-auction",
}


def get_project_card(project_id: str) -> ProjectCardData | None:
    """Lookup authoritative project card by exact ID or common alias."""
    clean_id = project_id.strip().lower()
    if clean_id in PROJECT_CATALOG:
        return PROJECT_CATALOG[clean_id]
    if clean_id in PROJECT_ALIASES:
        canonical_id = PROJECT_ALIASES[clean_id]
        return PROJECT_CATALOG.get(canonical_id)
    return None
