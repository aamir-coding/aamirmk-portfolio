"""Build the social preview image with bundled Pillow."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend/public"


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
    social()
    print("Built one 1200x630 social PNG.")
