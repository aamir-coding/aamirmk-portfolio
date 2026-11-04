"""Versioned evaluation inputs and provisional expectations, never model scores."""

from __future__ import annotations

import json
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1, pattern=r"\S")]
Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")]
Split = Literal["development", "held_out"]


class CaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CaseTurn(CaseModel):
    role: Literal["user", "assistant"]
    content: Text = Field(max_length=6000)


class CaseOrigin(CaseModel):
    kind: Literal["legacy_seed", "authored", "synthetic_jd", "protocol_regression"]
    reference: Text


class ExpectedSources(CaseModel):
    mode: Literal["all_relevant", "any_of", "none"]
    ids: list[Identifier] = Field(default_factory=list)

    @model_validator(mode="after")
    def unambiguous_source_set(self) -> Self:
        if len(self.ids) != len(set(self.ids)):
            raise ValueError("Duplicate source IDs")
        if (self.mode == "none") != (not self.ids):
            raise ValueError("Source IDs are required except for mode=none")
        return self


class CaseChecks(CaseModel):
    sources: ExpectedSources
    must_include: list[Text] = Field(default_factory=list)
    must_not_include: list[Text] = Field(default_factory=list)
    support_expectations: list[Text] = Field(min_length=1)
    expect_refusal: bool | None = None
    expected_error: (
        Literal["premature_eof", "malformed_event", "extraction_error"] | None
    ) = None


class EvalCase(CaseModel):
    id: Identifier
    version: int = Field(ge=1, strict=True)
    group_id: Identifier
    split: Split
    category: Literal[
        "factual",
        "hr",
        "technical",
        "off_topic",
        "refusal",
        "adversarial",
        "false_premise",
        "follow_up",
        "fit",
        "protocol",
    ]
    target: Literal["chat", "fit", "protocol"]
    origin: CaseOrigin
    label_status: Literal["provisional", "human_reviewed"] = "provisional"
    review_reference: Text | None = None
    conversation: list[CaseTurn] = Field(min_length=1, max_length=10)
    checks: CaseChecks
    transport_scenario: (
        Literal["truncated_after_token", "invalid_event_json"] | None
    ) = None

    @model_validator(mode="after")
    def coherent_case(self) -> Self:
        if self.label_status == "human_reviewed" and not self.review_reference:
            raise ValueError("Human review requires a review reference")
        if self.split == "held_out" and self.origin.kind == "legacy_seed":
            raise ValueError("A known development seed cannot become held-out")
        if self.conversation[-1].role != "user" or any(
            turn.role != ("user" if i % 2 == 0 else "assistant")
            for i, turn in enumerate(self.conversation)
        ):
            raise ValueError("Conversation must alternate from user and end with user")
        if self.target == "fit" and (
            self.category != "fit"
            or len(self.conversation) != 1
            or len(self.conversation[0].content.strip()) < 50
        ):
            raise ValueError("Fit cases require one JD of at least 50 characters")
        if (self.category == "fit") != (self.target == "fit") or (
            (self.category == "protocol") != (self.target == "protocol")
        ):
            raise ValueError(
                "Fit/protocol categories must match their execution target"
            )
        if (self.target == "protocol") != (self.transport_scenario is not None):
            raise ValueError("Only protocol cases require a transport scenario")
        if self.target == "chat" and (
            len(self.conversation[-1].content) > 2000
            or any(len(turn.content) > 4000 for turn in self.conversation[:-1])
        ):
            raise ValueError("Chat conversation exceeds production input limits")
        return self


class CaseSuite(CaseModel):
    version: Text
    cases: list[EvalCase] = Field(min_length=1)

    @model_validator(mode="after")
    def prevent_split_leakage(self) -> Self:
        ids: set[str] = set()
        groups: dict[str, str] = {}
        conversations: dict[str, str] = {}
        for case in self.cases:
            if case.id in ids:
                raise ValueError(f"Duplicate case ID: {case.id}")
            ids.add(case.id)
            if case.group_id in groups and groups[case.group_id] != case.split:
                raise ValueError("Case group overlap between development and held-out")
            groups[case.group_id] = case.split
            conversation = json.dumps(
                [
                    [turn.role, " ".join(turn.content.casefold().split())]
                    for turn in case.conversation
                ]
            )
            if conversation in conversations:
                raise ValueError("Duplicate conversation or split overlap")
            conversations[conversation] = case.split
        return self
