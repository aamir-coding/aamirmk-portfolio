"""Pre-evaluated authoritative golden benchmarks for curated sample JDs.

Provides instant, zero-cost, zero-latency evaluation snapshots for recruiter
exploration while eliminating repetitive LLM token consumption on sample roles.
"""

from __future__ import annotations

from app.fit.models import (
    FitReport,
    FitScoreSummary,
    JudgedRequirement,
    Requirement,
)

GOLDEN_BENCHMARK_REPORTS: dict[str, FitReport] = {
    "01-fullstack-ai-engineer": FitReport(
        role_title="Full-Stack AI Engineer",
        jd_hash=("7e63e2ed760845469ee1b07276536a6c3f8270a71f2d45f957d95d34fc353d7c"),
        score=FitScoreSummary(
            must_have_total=5,
            must_have_strong=5,
            must_have_partial=0,
            must_have_gap=0,
            nice_to_have_total=2,
            nice_to_have_strong=2,
            nice_to_have_partial=0,
            nice_to_have_gap=0,
            total_requirements=7,
            overall_fit="Strong Match",
            headline=(
                "Strong Match: Evidences 5 of 5 core criteria and 2 of 2"
                " preferred skills."
            ),
        ),
        requirements=[
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Strong proficiency in Python and async web frameworks"
                        " (FastAPI preferred)"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-backend", "projects-portfolio"],
                explanation=(
                    "Architected asynchronous FastAPI backend with native SSE"
                    " streaming and dependency injection."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience developing single-page web"
                        " applications with React, TypeScript, and modern CSS"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-frontend", "projects-entropy-oj"],
                explanation=(
                    "Built React/TypeScript single-page applications with token"
                    " design systems and responsive ergonomics."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Demonstrated experience building RAG workflows,"
                        " embedding generation, and semantic retrieval"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-retrieval", "projects-portfolio"],
                explanation=(
                    "Implemented Okapi BM25 and FastEmbed ONNX dense hybrid RAG"
                    " with Reciprocal Rank Fusion."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Practical experience with function calling, structured"
                        " LLM outputs, and streaming protocols (SSE /"
                        " WebSockets)"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-backend", "projects-portfolio"],
                explanation=(
                    "Engineered two-turn tool dispatch loop, Zod runtime"
                    " boundary contracts, and POST SSE client."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text="Hands-on containerization experience with Docker",
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-deployment"],
                explanation=(
                    "Containerized multi-service platforms using Docker"
                    " multi-stage builds and minimal runtime images."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Experience building automated evaluation suites for"
                        " LLM retrieval and response accuracy"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-evals"],
                explanation=(
                    "Created automated retrieval evals benchmarking Hit Rate@5"
                    " (100%) and MRR (0.88) across 45 queries."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-7",
                    text=(
                        "Familiarity with client-side accessibility (WCAG),"
                        " keyboard navigation, and bundle size optimization"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-frontend"],
                explanation=(
                    "Maintains WCAG contrast, ARIA landmarks, focus traps, and"
                    " strict <200 KB gzipped bundle budget."
                ),
            ),
        ],
        summary=(
            "Aamir exhibits direct verified alignment with Full-Stack AI"
            " Engineer requirements across FastAPI backend architecture,"
            " React/TypeScript frontends, and hybrid RAG retrieval. His"
            " production systems reflect proven mastery of structured tool"
            " calling, Docker deployment, and strict bundle preservation. He"
            " meets all core qualifications with strong receipts."
        ),
        cached=True,
    ),
    "02-backend-python-engineer": FitReport(
        role_title="Backend Software Engineer (Python / FastAPI)",
        jd_hash=("9b173c544f704af7198be68bc9fb2ae81ab53c5d0c782530a00652e0ec805111"),
        score=FitScoreSummary(
            must_have_total=5,
            must_have_strong=5,
            must_have_partial=0,
            must_have_gap=0,
            nice_to_have_total=2,
            nice_to_have_strong=1,
            nice_to_have_partial=1,
            nice_to_have_gap=0,
            total_requirements=7,
            overall_fit="Strong Match",
            headline=(
                "Strong Match: Evidences 5 of 5 core criteria with 1 partial"
                " alignment on enterprise cloud VMs."
            ),
        ),
        requirements=[
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Strong programming background in Python with"
                        " experience in FastAPI or Django"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-backend"],
                explanation=(
                    "Deep expertise in modern Python 3.12+, Pydantic v2"
                    " schemas, and FastAPI asynchronous web services."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience with PostgreSQL, relational data"
                        " modeling, and query performance"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-databases", "projects-entropy-oj"],
                explanation=(
                    "Designed normalized relational schemas, managed migrations"
                    " with Alembic, and optimized SQL queries."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Experience implementing background workers and caching"
                        " using Redis and asynchronous queue frameworks"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-backend", "projects-entropy-oj"],
                explanation=(
                    "Built asynchronous BullMQ and Redis task processing"
                    " workers for distributed code execution."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Proficiency in Docker containerization and Git-based"
                        " collaborative workflows"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-deployment"],
                explanation=(
                    "Employs Docker containerization, semantic commit"
                    " standards, and automated GitHub Actions CI."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text=(
                        "Rigorous testing mindset with experience writing unit"
                        " and integration tests using pytest"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-backend", "skills-evals"],
                explanation=(
                    "Authored 177+ pytest tests with async fixtures,"
                    " dependency overrides, and zero-cost fakes."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Experience deploying and configuring cloud virtual"
                        " machines (Microsoft Azure or AWS)"
                    ),
                    importance="nice_to_have",
                    type="experience",
                ),
                verdict="partial",
                evidence_chunk_ids=["skill-ramp-up-narratives"],
                explanation=(
                    "Primary deployments reside on Render and Vercel; actively"
                    " ramping up on AWS EC2/VPC infrastructure."
                ),
                ramp_up=(
                    "Extrapolates from Linux VM administration and Docker"
                    " containerization to cloud VPC and EC2 environments."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-7",
                    text=(
                        "Understanding of reverse-proxy routing, CORS"
                        " policies, and rate-limiting middleware"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-security", "skills-backend"],
                explanation=(
                    "Implemented sliding-window IP rate limiters, RFC headers,"
                    " and origin-validated CORS middleware."
                ),
            ),
        ],
        summary=(
            "Aamir delivers complete verified production coverage across"
            " asynchronous Python backend services, PostgreSQL data modeling,"
            " Redis caching, and pytest suites. His containerization and"
            " security middleware directly match production backend standards."
            " His partial gap in AWS VMs is supported by a credible Linux"
            " containerization ramp-up plan."
        ),
        cached=True,
    ),
    "03-genai-application-developer": FitReport(
        role_title="Generative AI Application Developer",
        jd_hash=("79a0a2d49a2876a4ed002f511edffb3c007a7131156cf35f4b95abbc6b4fe39c"),
        score=FitScoreSummary(
            must_have_total=4,
            must_have_strong=3,
            must_have_partial=0,
            must_have_gap=1,
            nice_to_have_total=2,
            nice_to_have_strong=1,
            nice_to_have_partial=0,
            nice_to_have_gap=1,
            total_requirements=6,
            overall_fit="Partial Match",
            headline=(
                "Partial Match: Covers 3 of 4 must-haves; AWS enterprise"
                " infrastructure represents an honest gap."
            ),
        ),
        requirements=[
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Strong proficiency in Python or TypeScript for backend"
                        " application development"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-backend", "skills-frontend"],
                explanation=(
                    "Full-stack proficiency building production services in"
                    " both Python/FastAPI and TypeScript."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience with LLM APIs, prompt"
                        " engineering, structured JSON schema output, and tool"
                        " calling"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-backend", "projects-portfolio"],
                explanation=(
                    "Built multi-turn Groq tool dispatch loops and strict JSON"
                    " schema structured output pipelines."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Demonstrated experience building semantic search,"
                        " hybrid retrieval, and chunking strategies"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-retrieval"],
                explanation=(
                    "Engineered hybrid BM25 + dense vector search with"
                    " Cormack's Reciprocal Rank Fusion."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Minimum 2 years of production hands-on experience"
                        " designing and operating AWS cloud infrastructure"
                        " (ECS, Lambda, S3, IAM)"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="gap",
                evidence_chunk_ids=["skill-ramp-up-narratives"],
                explanation=(
                    "No verified multi-year AWS production infrastructure"
                    " experience in portfolio facts."
                ),
                ramp_up=(
                    "Aamir is actively bridging AWS cloud concepts using"
                    " S3-compatible storage, IAM policies, and container"
                    " orchestration."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text=(
                        "Hands-on experience with Kubernetes cluster"
                        " operations, Helm charts, and container"
                        " orchestration"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=["skill-ramp-up-narratives"],
                explanation=(
                    "Docker-native background; no multi-node production"
                    " Kubernetes cluster management claimed."
                ),
                ramp_up=(
                    "Actively studying CKA curriculum fundamentals and"
                    " operating local kind/k3s test clusters."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Experience with automated LLM eval suites measuring"
                        " Hit Rate, Recall@K, and LLM-as-judge scoring"
                    ),
                    importance="nice_to_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["skills-evals"],
                explanation=(
                    "Authored dedicated automated retrieval eval suites"
                    " testing Hit Rate@K, MRR, and latency benchmarks."
                ),
            ),
        ],
        summary=(
            "Aamir exhibits strong, verifiable depth in core Generative AI"
            " engineering, structured tool loops, and hybrid RAG retrieval."
            " The primary gap is multi-year AWS cloud infrastructure and"
            " production Kubernetes management, which are honestly acknowledged"
            " with concrete ramp-up plans. His background in automated eval"
            " suites brings immediate value to the role."
        ),
        cached=True,
    ),
    "04-embedded-firmware-engineer": FitReport(
        role_title="Embedded Systems & Firmware Engineer (C / C++)",
        jd_hash=("3ab110ed8b02a04be821bb8f689c241852f3b3025071697ceabe3750bc7f622d"),
        score=FitScoreSummary(
            must_have_total=4,
            must_have_strong=0,
            must_have_partial=0,
            must_have_gap=4,
            nice_to_have_total=2,
            nice_to_have_strong=0,
            nice_to_have_partial=0,
            nice_to_have_gap=2,
            total_requirements=6,
            overall_fit="Low Match",
            headline=(
                "Low Match: Covers 0 of 4 must-haves; specialized hardware"
                " and low-level firmware background required."
            ),
        ),
        requirements=[
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Deep expertise in bare-metal embedded C and C++"
                        " programming for resource-constrained microcontrollers"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No bare-metal microcontroller C or embedded C++ firmware"
                    " verified in portfolio facts."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience developing under Real-Time"
                        " Operating Systems (FreeRTOS, Zephyr)"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No real-time embedded operating system (RTOS) development"
                    " verified in candidate dossier."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Direct experience configuring low-level serial"
                        " peripherals: SPI, I2C, UART, DMA controllers"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No physical microcontroller hardware peripheral"
                    " configuration evidenced in candidate dossier."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Proven track record of board bring-up and physical"
                        " hardware lab debugging with oscilloscopes"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "Candidate background is software-focused; no physical"
                    " board bring-up or lab instrument debugging claimed."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text=(
                        "Experience designing PCB schematics and layout using"
                        " KiCAD or Altium Designer"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No electrical schematic capture or PCB physical layout"
                    " design experience claimed."
                ),
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Familiarity with motor control algorithms (PID"
                        " controllers, PWM signal generation)"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No embedded motor control or hardware PWM signal"
                    " generation experience claimed."
                ),
            ),
        ],
        summary=(
            "Aamir's engineering background is concentrated in distributed web"
            " systems, asynchronous backend microservices, and generative AI"
            " application architectures rather than bare-metal embedded"
            " firmware. He does not claim experience with real-time operating"
            " systems (FreeRTOS), microcontroller peripherals, or physical"
            " hardware lab instruments. This position requires specialized"
            " electrical engineering competencies outside his production focus."
        ),
        cached=True,
    ),
}
