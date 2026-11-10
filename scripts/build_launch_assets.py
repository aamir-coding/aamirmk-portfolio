"""Author launch files with bundled ReportLab/Pillow, not application dependencies."""

import re
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend/public"


def markup(text: str) -> str:
    return re.sub(
        r"\[([^]]+)\]\((https?://[^)]+|mailto:[^)]+)\)",
        r'<a href="\2" color="#18375b">\1</a>',
        escape(text),
    )


def resume() -> None:
    styles = {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=colors.HexColor("#18375b"),
            spaceAfter=8,
        ),
        "heading": ParagraphStyle(
            "heading",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=3,
            textColor=colors.HexColor("#18375b"),
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9, leading=12, spaceAfter=5
        ),
    }
    story = []
    for line in (PUBLIC / "resume-draft.md").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        key = (
            "title"
            if line.startswith("# ")
            else "heading"
            if line.startswith("## ")
            else "body"
        )
        story.append(Paragraph(markup(line.lstrip("# ")), styles[key]))
    SimpleDocTemplate(
        str(PUBLIC / "resume-draft.pdf"),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=35,
        bottomMargin=35,
        title="Aamir Mohammed Khan - Resume Draft",
        author="Aamir Mohammed Khan",
    ).build(story)


def social() -> None:
    canvas = Image.new("RGB", (1200, 630), "#18181b")
    draw = ImageDraw.Draw(canvas)
    fonts = Path("C:/Windows/Fonts")
    title = ImageFont.truetype(str(fonts / "georgia.ttf"), 61)
    body = ImageFont.truetype(str(fonts / "segoeui.ttf"), 29)
    small = ImageFont.truetype(str(fonts / "segoeui.ttf"), 24)
    draw.rectangle((35, 35, 1165, 595), outline="#52525b", width=2)
    draw.text((80, 100), "Candidate portfolio", font=small, fill="#d4d4d8")
    draw.text((80, 190), "Aamir Mohammed Khan", font=title, fill="#f4f4f5")
    draw.text(
        (80, 285), "AI Systems & Full-Stack Engineering", font=body, fill="#60a5fa"
    )
    draw.line((80, 365, 1120, 365), fill="#52525b", width=2)
    draw.text(
        (80, 405),
        "Projects, experience and an interactive AI assistant",
        font=small,
        fill="#f4f4f5",
    )
    draw.text(
        (80, 455),
        "FastAPI / Hybrid retrieval / React / TypeScript",
        font=small,
        fill="#d4d4d8",
    )
    draw.text((80, 535), "aamirmk-portfolio.vercel.app", font=small, fill="#d4d4d8")
    canvas.save(PUBLIC / "og-image.png", optimize=True)


if __name__ == "__main__":
    resume()
    social()
    print("Built one draft resume PDF and one 1200x630 social PNG.")
