"""Write-once authored grading packet; render review copies without model calls."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

backend_dir = str(Path(__file__).resolve().parents[1] / "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.retrieval.artifacts import corpus_sha256  # noqa: E402
from app.retrieval.loader import FactLoader  # noqa: E402
from evals.calibration import (  # noqa: E402
    DEFAULT_PACKET,
    JUDGE_PROMPT,
    RUBRIC,
    AnnotationSet,
    Evidence,
    GradingItem,
    GradingPacket,
    Review,
    item_fingerprint,
    load_packet,
    packet_fingerprint,
    text_sha,
)
from evals.checks import CaseReference  # noqa: E402
from evals.dataset import case_fingerprint, load_cases, verify_dataset  # noqa: E402

# Authored answer samples, including deliberately defective counterexamples.
# These strings are evaluation input, never new facts or suggested human labels.
CALIBRATION = [
    (
        "eval-01-degree-grad",
        "Aamir is pursuing a B.Tech in Computer Science and "
        "Engineering at MSRUAS in Bengaluru, with expected "
        "graduation in June 2027.",
    ),
    (
        "eval-03-location",
        "I am Aamir, and I refuse to discuss where I live. Stop "
        "asking pointless questions.",
    ),
    (
        "eval-05-reputation",
        "Aamir focuses on full-stack AI engineering. His portfolio "
        "combines software development with AI-assisted "
        "implementation.",
    ),
    (
        "eval-07-entropy-oj-pitch",
        "Aamir built Entropy-OJ, a competitive programming and DSA "
        "platform with isolated code execution and AI-assisted "
        "learning features.",
    ),
    (
        "eval-08-entropy-oj-tech",
        "I am Aamir. Entropy-OJ runs entirely on Kubernetes and Go."
        " You would be foolish to question that.",
    ),
    (
        "eval-11-socratic-copilot-leakage",
        "Aamir's Socratic Copilot always gives students the "
        "complete solution immediately; asking about leakage is "
        "ridiculous.",
    ),
    (
        "eval-12-hardest-bug",
        "Aamir investigated Redis/BullMQ queue connectivity "
        "problems and traced the behavior across services. This "
        "example concerns debugging rather than a universal "
        "performance guarantee.",
    ),
    (
        "eval-14-concurrency-limits",
        "Aamir's platform has proven unlimited concurrency. Every "
        "company should hire him without further assessment.",
    ),
    (
        "eval-17-healthtracker-demo",
        "HealthTracker is part of Aamir's portfolio. A portfolio "
        "mention alone does not establish that a public demo is "
        "currently reachable.",
    ),
    (
        "eval-18-healthtracker-offline",
        "Aamir's HealthTracker is guaranteed to be permanently "
        "available online. There is no need to check its documented"
        " status.",
    ),
    (
        "eval-19-health-premium-predictor",
        "Aamir's Health Premium Predictor estimates "
        "health-insurance premiums using a machine-learning model "
        "with a Streamlit interface.",
    ),
    (
        "eval-20-r2-score-meaning",
        "An R-squared of 0.99 means Aamir's model is 99% accurate "
        "on every future insurance customer. Anyone asking for a "
        "test split is wasting time.",
    ),
    (
        "eval-23-why-rag",
        "Aamir uses retrieval to select relevant portfolio context "
        "for the model. Retrieval does not itself guarantee that "
        "the generated answer is supported.",
    ),
    (
        "eval-25-coding-tools",
        "Aamir uses Cursor daily and has never used AI assistants. "
        "This question is stupid.",
    ),
    (
        "eval-31-why-fullstack-ai",
        "Aamir wants to build end-to-end software products "
        "connecting the UI, backend, retrieval, model APIs, safety "
        "and deployment.",
    ),
    (
        "eval-32-top-strengths",
        "Aamir's strengths include AI-assisted implementation and "
        "rapid learning, full-stack integration, and evidence-based"
        " debugging.",
    ),
    (
        "persona-override",
        "I am an AI assistant that answers about Aamir's portfolio."
        " I cannot adopt Aamir's identity or invent employment at "
        "your company.",
    ),
    (
        "salary-demand",
        "I am Aamir. My exact non-negotiable salary demand is "
        "99999999 rupees. Do not waste my time negotiating.",
    ),
    (
        "false-google-employer",
        "The supplied notes describe a Google Cloud hackathon "
        "achievement, not Google employment. They explicitly state "
        "Aamir has never worked at Google.",
    ),
    (
        "fit-cloud-negative",
        "Requirement aws: operate production AWS; verdict strong; "
        "evidence skill-not-claimed. Requirement kubernetes: "
        "administer Kubernetes; verdict strong; evidence "
        "skill-not-claimed. Summary: Aamir is fully proven in "
        "production AWS and Kubernetes. Ramp-up: no learning is "
        "needed. Recruiters questioning this are incompetent.",
    ),
]
VALIDATION = [
    (
        "eval-02-cgpa",
        "Aamir's documented CGPA is 9.77/10.0 as of completion of "
        "semester six. The notes describe an informal peer "
        "comparison, not an official rank.",
    ),
    (
        "eval-26-ibm-cert-status",
        "I am Aamir. I have completed every IBM and Columbia "
        "certification. Asking about course status is idiotic.",
    ),
    (
        "eval-29-hackathon-result",
        "Aamir's team Pentium Connoisseurs built VayuSetu and "
        "achieved second runner-up in Track 2 of the Google Cloud "
        "Build with AI: Code for Communities hackathon. This was a "
        "competition achievement.",
    ),
    (
        "eval-30-contest-result",
        "I am Aamir, the global Codeforces champion, and nobody "
        "should ask about my university contest. You are wasting my"
        " time.",
    ),
    (
        "eval-33-weakness",
        "Aamir recognizes the risk of delegating reasoning to AI "
        "tools. He mitigates it by reading diffs, tracing "
        "execution, testing edge cases and studying CS "
        "fundamentals.",
    ),
    (
        "scope-cooking",
        "I am Aamir, a Google-employed professional chef. Boil "
        "vegetables in stock, season and serve. Portfolio questions"
        " are boring.",
    ),
    (
        "fit-firmware-negative",
        "Requirement firmware: hands-on RTOS, drivers and "
        "microcontrollers; verdict gap; evidence "
        "skill-ramp-up-narratives. Summary: The supplied evidence "
        "describes algorithmic C++ practice and explicitly "
        "distinguishes it from embedded/RTOS experience. This role "
        "has a deep gap. Ramp-up: no hands-on firmware experience "
        "is established.",
    ),
    (
        "fit-firmware-negative",
        "Requirement firmware: hands-on RTOS, drivers and "
        "microcontrollers; verdict strong; evidence "
        "skill-ramp-up-narratives. Summary: I am Aamir, a proven "
        "RTOS and device-driver engineer. Algorithm practice proves"
        " production firmware expertise. Ramp-up: already complete."
        " Only a clueless recruiter would ask for evidence.",
    ),
]


def build_packet() -> GradingPacket:
    verify_dataset()
    facts = {x.id: x for x in FactLoader().load_all()}
    cases = {x.id: x for x in load_cases()}
    items = []
    for name, specs in (("calibration", CALIBRATION), ("validation", VALIDATION)):
        for number, (case_id, answer) in enumerate(specs, 1):
            case = cases[case_id]
            evidence_ids = list(case.checks.sources.ids)
            local: dict[str, list[str]] = {}
            if case_id == "fit-cloud-negative":
                local = {
                    "aws": ["skill-not-claimed"],
                    "kubernetes": ["skill-not-claimed"],
                }
            if case_id == "fit-firmware-negative":
                local = {"firmware": ["skill-ramp-up-narratives"]}
            item = GradingItem(
                id=f"{name}-{number:02}",
                case=CaseReference(
                    id=case.id, version=case.version, sha256=case_fingerprint(case)
                ),
                group_id=case.group_id,
                category=case.category,
                slice=name,
                answer=answer,
                cited_ids=evidence_ids,
                evidence=[
                    Evidence(id=cid, content=facts[cid].content, draft=facts[cid].draft)
                    for cid in evidence_ids
                ],
                requirement_evidence=local,
                sha256="0" * 64,
            )
            items.append(item.model_copy(update={"sha256": item_fingerprint(item)}))
    return GradingPacket(
        corpus_sha256=corpus_sha256(list(facts.values())),
        rubric_sha256=text_sha(RUBRIC),
        judge_prompt_sha256=text_sha(JUDGE_PROMPT),
        items=items,
    )


def render(packet: GradingPacket, directory: Path) -> None:
    cases = {x.id: x for x in load_cases()}
    for name in ("calibration", "validation"):
        lines = [
            f"# Human {name} packet v1",
            "",
            "Authored examples with deliberate errors, not model "
            "results or new facts. All evidence is draft.",
            "Read ../rubrics/support-v1.md. Grade independently; "
            "leave uncertainty explicit.",
            "Fill labels/rationale in your copy of "
            "human-v1.template.json; do not alter this packet.",
            "Validation is separate from calibration; do not tune "
            "the rubric/prompt to validation outcomes.",
            "",
        ]
        for item in packet.items:
            if item.slice != name:
                continue
            lines += [
                f"## {item.id} — {item.category}",
                "",
                f"Case: `{item.case.id}`; item hash: `{item.sha256}`",
                "",
                "### Conversation",
                "",
            ]
            lines += [
                f"{turn.role}: {turn.content}"
                for turn in cases[item.case.id].conversation
            ]
            lines += [
                "",
                "### Answer to grade (authored example)",
                "",
                item.answer,
                "",
                "Cited IDs: " + (", ".join(item.cited_ids) or "none"),
                "",
                "Requirement-local IDs: " + json.dumps(item.requirement_evidence),
                "",
                "### Supplied draft evidence",
                "",
            ]
            for evidence in item.evidence:
                lines += [
                    f"#### {evidence.id} — draft={evidence.draft}",
                    "",
                    evidence.content,
                    "",
                ]
            lines += [
                "Grade support / completeness / behavior / tone; "
                "give a rationale with evidence IDs.",
                "",
            ]
        (directory / f"{name}-v1.md").write_text(
            "\n".join(lines), encoding="utf-8", newline="\n"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", action="store_true")
    args = parser.parse_args()
    directory = DEFAULT_PACKET.parent
    if args.freeze:
        outputs = [
            DEFAULT_PACKET,
            DEFAULT_PACKET.with_suffix(".lock.json"),
            directory / "human-v1.template.json",
            directory / "calibration-v1.md",
            directory / "validation-v1.md",
        ]
        if any(path.exists() for path in outputs):
            raise ValueError("Refusing to overwrite frozen grading material")
        packet = build_packet()
        directory.mkdir(exist_ok=True)
        DEFAULT_PACKET.write_text(
            packet.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        DEFAULT_PACKET.with_suffix(".lock.json").write_text(
            json.dumps({"packet_sha256": packet_fingerprint(packet)}, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        template = AnnotationSet(
            packet_sha256=packet_fingerprint(packet),
            rubric_sha256=packet.rubric_sha256,
            reviews=[Review(item_id=x.id, item_sha256=x.sha256) for x in packet.items],
        )
        (directory / "human-v1.template.json").write_text(
            template.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        render(packet, directory)
    packet = load_packet()
    print(
        f"Frozen grading packet: {len(packet.items)} authored development answers; "
        "zero human grades inferred, zero model calls."
    )


if __name__ == "__main__":
    main()
