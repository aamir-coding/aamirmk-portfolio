"""Identify standalone questions about schooling, education and achievements."""

import re
from enum import Enum

from app.retrieval.models import FactChunk


class Overview(Enum):
    SCHOOL = (
        "schooling CBSE class 10 class 12 school background "
        "secondary higher secondary school percentage"
    )
    EDUCATION = (
        "education history degree university CGPA school background "
        "CBSE class 10 class 12"
    )
    ACHIEVEMENTS = (
        "achievements awards hackathon competition scholarship academic excellence"
    )

    def includes(self, fact: FactChunk) -> bool:
        if self is Overview.ACHIEVEMENTS:
            return fact.type == "achievement"
        if fact.type != "education":
            return False
        return "school" in fact.tags or (
            self is Overview.EDUCATION and "degree" in fact.tags
        )


_QUESTION = re.compile(
    r"(?:(?:please |can you |could you )*(?:tell me about |tell me |list |"
    r"summari[sz]e |show me |give me |what (?:are|were|is|was) |"
    r"what about |how about ))?"
    r"(?:(?:all|of|the|some|his|aamir(?: mohammed khan)?(?:'s)?|key|notable|major|"
    r"top|best|main|biggest|formal|full|entire) )*"
    r"(?P<topic>achievements?|accomplishments?|awards?|schooling|school|educational|education|academic)"
    r"(?: (?:history|background|details|qualifications|records?))?"
    r"(?: (?:so far|to date|please))?"
)


def overview_for(question: str) -> Overview | None:
    words = " ".join(question.casefold().replace("’", "'").split()).strip(" .!?,")
    match = _QUESTION.fullmatch(words)
    if not match:
        return None
    topic = match["topic"]
    if topic in {"school", "schooling"}:
        return Overview.SCHOOL
    if topic in {"education", "educational", "academic"}:
        return Overview.EDUCATION
    return Overview.ACHIEVEMENTS
