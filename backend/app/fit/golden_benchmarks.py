"""Curated sample assessments grounded in the current fact files.

These are conservative, manually maintained snapshots, not live evaluations or
independently calibrated ground truth. Draft fact approval remains tracked.
"""

from app.fit.models import FitReport, JudgedRequirement, Requirement
from app.fit.scorer import compute_fit_summary


def _report(
    role_title: str, jd_hash: str, requirements: list[JudgedRequirement], summary: str
) -> FitReport:
    return FitReport(
        role_title=role_title,
        jd_hash=jd_hash,
        score=compute_fit_summary(requirements),
        requirements=requirements,
        summary=summary,
        cached=True,
    )


GOLDEN_BENCHMARK_REPORTS: dict[str, FitReport] = {
    "01-fullstack-ai-engineer": _report(
        "Full-Stack AI Engineer",
        "7e63e2ed760845469ee1b07276536a6c3f8270a71f2d45f957d95d34fc353d7c",
        [
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Strong proficiency in Python and async web frameworks "
                        "(FastAPI preferred)"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "skill-frameworks-libraries",
                    "proj-ai-assistant-architecture",
                ],
                explanation=(
                    "Working FastAPI exposure; the portfolio documents Python, "
                    "Pydantic and SSE."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience developing single-page web applications "
                        "with React, TypeScript, and modern CSS"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["proj-entropy-oj-stack"],
                explanation=(
                    "Entropy-OJ uses React 19, TypeScript and Vite for its "
                    "responsive coding workspace."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Demonstrated experience building RAG workflows, embedding "
                        "generation, and semantic retrieval"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "proj-ai-assistant-design",
                    "skill-ai-llm-engineering",
                ],
                explanation=(
                    "Aamir implemented BM25, FastEmbed ONNX embeddings, and "
                    "rank fusion in the shipped portfolio. The evidence covers "
                    "one portfolio project."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Practical experience with function calling, structured LLM "
                        "outputs, and streaming protocols (SSE / WebSockets)"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "proj-ai-assistant-architecture",
                    "skill-ai-llm-engineering",
                ],
                explanation=(
                    "The portfolio ships Starlette SSE, a validated project-card "
                    "tool, and structured JD fit outputs. The streaming "
                    "implementation uses SSE."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text="Hands-on containerization experience with Docker",
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skill-cloud-devops-tools"],
                explanation=(
                    "Docker is used in Entropy-OJ worker deployment configuration."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Experience building automated evaluation suites for LLM "
                        "retrieval and response accuracy"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "skill-ai-llm-engineering",
                    "proj-ai-assistant-status",
                ],
                explanation=(
                    "The portfolio has automated retrieval metrics and contract "
                    "replay. Independent response accuracy remains unverified."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-7",
                    text=(
                        "Familiarity with client-side accessibility (WCAG), keyboard "
                        "navigation, and bundle size optimization"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "Verified WCAG audit results and accessibility optimization "
                    "experience are not established in the current facts."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
        ],
        (
            "Aamir shipped React/TypeScript, FastAPI, hybrid RAG, and an "
            "interactive project-card tool. His portfolio has automated "
            "retrieval and replay checks. Independent answer accuracy and "
            "WCAG audit results need further verification."
        ),
    ),
    "02-backend-python-engineer": _report(
        "Backend Software Engineer (Python / FastAPI)",
        "9b173c544f704af7198be68bc9fb2ae81ab53c5d0c782530a00652e0ec805111",
        [
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Strong programming background in Python with experience in "
                        "FastAPI or Django"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=[
                    "skill-frameworks-libraries",
                    "skill-programming-languages",
                ],
                explanation=(
                    "Working Python, FastAPI and Django experience is documented."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience with PostgreSQL, relational data "
                        "modeling, and query performance"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="partial",
                evidence_chunk_ids=["skill-databases"],
                explanation=(
                    "Aamir used PostgreSQL in the Django auction project and "
                    "modeled recruiter data with SQLAlchemy and Alembic. "
                    "Query-performance expertise needs further evidence."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Experience implementing background workers and caching using"
                        " Redis and asynchronous queue frameworks"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=["proj-entropy-oj-stack"],
                explanation=(
                    "Entropy-OJ uses Redis and BullMQ for asynchronous judging "
                    "and background classification."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Proficiency in Docker containerization and Git-based "
                        "collaborative workflows"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=["skill-cloud-devops-tools"],
                explanation=(
                    "Docker worker deployment and Git/GitHub source-control "
                    "workflows are documented."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text=(
                        "Rigorous testing mindset with experience writing unit and "
                        "integration tests using pytest"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "A pytest unit/integration testing track record is not "
                    "established by the current curated facts."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Experience deploying and configuring cloud virtual machines "
                        "(Microsoft Azure or AWS)"
                    ),
                    importance="nice_to_have",
                    type="experience",
                ),
                verdict="strong",
                evidence_chunk_ids=[
                    "skill-cloud-devops-tools",
                    "proj-entropy-oj-stack",
                ],
                explanation=(
                    "Entropy-OJ worker and Redis run on an Azure VM; AWS service "
                    "use is not claimed."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-7",
                    text=(
                        "Understanding of reverse-proxy routing, CORS policies, and "
                        "rate-limiting middleware"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "skill-ai-llm-engineering",
                    "proj-ai-assistant-architecture",
                ],
                explanation=(
                    "The portfolio implements request limits and trusted-proxy "
                    "configuration. The deployed proxy topology needs further "
                    "verification."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
        ],
        (
            "Aamir has documented Python/Django, Redis/BullMQ, Docker and"
            " Azure VM experience. PostgreSQL and security depth only "
            "partially match the requested scope. A pytest testing track "
            "record requires verification."
        ),
    ),
    "03-genai-application-developer": _report(
        "Generative AI Application Developer",
        "79a0a2d49a2876a4ed002f511edffb3c007a7131156cf35f4b95abbc6b4fe39c",
        [
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Strong proficiency in Python or TypeScript for backend "
                        "application development"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="strong",
                evidence_chunk_ids=[
                    "skill-programming-languages",
                    "skill-frameworks-libraries",
                ],
                explanation=(
                    "Working Python, TypeScript, FastAPI and Node.js application "
                    "experience is documented."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience with LLM APIs, prompt engineering, "
                        "structured JSON schema output, and tool calling"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "skill-ai-llm-engineering",
                    "proj-ai-assistant-architecture",
                ],
                explanation=(
                    "The shipped assistant validates model tool arguments for "
                    "project cards and structured outputs for JD fit reports."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Demonstrated experience building semantic search, hybrid "
                        "retrieval, and chunking strategies"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "proj-ai-assistant-design",
                    "skill-ai-llm-engineering",
                ],
                explanation=(
                    "The shipped assistant indexes curated Markdown and YAML "
                    "chunks with BM25 and FastEmbed ONNX embeddings."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Minimum 2 years of production hands-on experience designing "
                        "and operating AWS cloud infrastructure (ECS, Lambda, S3, "
                        "IAM)"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="gap",
                evidence_chunk_ids=["skill-not-claimed"],
                explanation=(
                    "No specific AWS service use or multi-year AWS operations is "
                    "established."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text=(
                        "Hands-on experience with Kubernetes cluster operations, Helm"
                        " charts, and container orchestration"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=["skill-not-claimed"],
                explanation="No hands-on Kubernetes experience is claimed.",
                ramp_up=(
                    "Proposed ramp-up: practise Pods, ConfigMaps, Deployments and"
                    " basic Helm with Minikube and official documentation; this "
                    "is not current hands-on experience."
                ),
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Experience with automated LLM eval suites measuring Hit "
                        "Rate, Recall@K, and LLM-as-judge scoring"
                    ),
                    importance="nice_to_have",
                    type="experience",
                ),
                verdict="partial",
                evidence_chunk_ids=[
                    "skill-ai-llm-engineering",
                    "proj-ai-assistant-status",
                ],
                explanation=(
                    "The portfolio measures retrieval and replays recorded "
                    "answers. Independent judge validation remains incomplete."
                ),
                ramp_up=(
                    "A proposed next step is a scoped exercise using official "
                    "documentation, tests and a review of limitations."
                ),
                downgraded=False,
            ),
        ],
        (
            "Aamir shipped hybrid retrieval, validated model tool calls, and "
            "structured job-fit outputs. The portfolio has offline retrieval "
            "and replay evaluation. AWS and Kubernetes experience and "
            "independent LLM evaluation remain gaps."
        ),
    ),
    "04-embedded-firmware-engineer": _report(
        "Embedded Systems & Firmware Engineer (C / C++)",
        "3ab110ed8b02a04be821bb8f689c241852f3b3025071697ceabe3750bc7f622d",
        [
            JudgedRequirement(
                requirement=Requirement(
                    id="req-1",
                    text=(
                        "Deep expertise in bare-metal embedded C and C++ programming "
                        "for resource-constrained microcontrollers"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No bare-metal microcontroller C or embedded C++ firmware "
                    "verified in portfolio facts."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-2",
                    text=(
                        "Hands-on experience developing under Real-Time Operating "
                        "Systems (FreeRTOS, Zephyr)"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No real-time embedded operating system (RTOS) development "
                    "verified in candidate dossier."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-3",
                    text=(
                        "Direct experience configuring low-level serial peripherals: "
                        "SPI, I2C, UART, DMA controllers"
                    ),
                    importance="must_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No physical microcontroller hardware peripheral "
                    "configuration evidenced in candidate dossier."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-4",
                    text=(
                        "Proven track record of board bring-up and physical hardware "
                        "lab debugging with oscilloscopes"
                    ),
                    importance="must_have",
                    type="experience",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "Candidate background is software-focused; no physical board "
                    "bring-up or lab instrument debugging claimed."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-5",
                    text=(
                        "Experience designing PCB schematics and layout using KiCAD "
                        "or Altium Designer"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No electrical schematic capture or PCB physical layout "
                    "design experience claimed."
                ),
                ramp_up=None,
                downgraded=False,
            ),
            JudgedRequirement(
                requirement=Requirement(
                    id="req-6",
                    text=(
                        "Familiarity with motor control algorithms (PID controllers, "
                        "PWM signal generation)"
                    ),
                    importance="nice_to_have",
                    type="skill",
                ),
                verdict="gap",
                evidence_chunk_ids=[],
                explanation=(
                    "No embedded motor control or hardware PWM signal generation "
                    "experience claimed."
                ),
                ramp_up=None,
                downgraded=False,
            ),
        ],
        (
            "Aamir's engineering background is concentrated in "
            "distributed web systems, asynchronous backend microservices,"
            " and generative AI application architectures rather than "
            "bare-metal embedded firmware. He does not claim experience "
            "with real-time operating systems (FreeRTOS), microcontroller"
            " peripherals, or physical hardware lab instruments. This "
            "position requires specialized electrical engineering "
            "competencies outside his production focus."
        ),
    ),
}
