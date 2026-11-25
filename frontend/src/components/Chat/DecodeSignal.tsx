import { useEffect, useRef } from "react";

const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+";
const stepMs = 60;
const steps = 10;
const randomGlyph = () => alphabet[Math.floor(Math.random() * alphabet.length)];

// The waiting and writing signals share a clock in CSS. No token or timer rerenders the transcript.
const tracks = Array.from({ length: 10 }, () => {
  const frames = Array.from({ length: steps }, randomGlyph);
  return [...frames, frames[0]].join("\n");
});

export function DecodeSignal({ phase = "waiting" }: { phase?: "waiting" | "cursor" }) {
  const count = phase === "waiting" ? tracks.length : 3;
  return <span className={`decode-signal decode-${phase}`} aria-hidden="true">
    {tracks.slice(0, count).map((frames, index) =>
      <span key={index} className="decode-column" data-frames={frames} />)}
  </span>;
}

// Use the rendered glyph boxes so a wrapped line or a bold opening keeps its exact typography.
function openingBoxes(prose: Element): DOMRect[] {
  const block = prose.querySelector("p, h1, h2, h3, h4, li");
  if (!block) return [];
  const nodes = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  const boxes: DOMRect[] = [];
  for (let node = nodes.nextNode(); node && boxes.length < steps; node = nodes.nextNode()) {
    if (node.parentElement?.closest("code, pre, [aria-hidden=true]")) continue;
    const text = node.nodeValue ?? "";
    for (const match of text.matchAll(/[A-Za-z0-9]/g)) {
      range.setStart(node, match.index);
      range.setEnd(node, match.index + 1);
      const box = range.getBoundingClientRect();
      if (box.width > 0) boxes.push(box);
      if (boxes.length === steps) break;
    }
  }
  return boxes;
}

export function DecryptedOpening() {
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const layer = ref.current;
    const host = layer?.parentElement;
    const prose = host?.querySelector(".chat-prose");
    if (!layer || !host || !prose || !window.IntersectionObserver) return;
    let timer: number | undefined;
    let nearOpening = false;

    const stop = () => {
      window.clearTimeout(timer);
      timer = undefined;
      layer.replaceChildren();
    };

    const play = () => {
      if (timer !== undefined || document.hidden || !layer.getClientRects().length) return;
      // A busy frame on first open should stretch the reveal, never skip its letters.
      let revealed = 0;
      const draw = () => {
        if (revealed >= steps || document.hidden || !layer.getClientRects().length) {
          stop();
          return;
        }
        const origin = layer.getBoundingClientRect();
        const boxes = openingBoxes(prose);
        const glyphs = boxes.slice(revealed).map(box => {
          const glyph = document.createElement("span");
          glyph.dataset.glyph = randomGlyph();
          Object.assign(glyph.style, {
            left: `${box.left - origin.left}px`, top: `${box.top - origin.top}px`,
            width: `${box.width}px`, height: `${box.height}px`,
            fontSize: `${Math.min(box.height * .82, box.width * 1.6)}px`,
          });
          return glyph;
        });
        layer.replaceChildren(...glyphs);
        revealed++;
        timer = window.setTimeout(draw, stepMs);
      };
      draw();
    };

    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) { play(); observer.disconnect(); }
    });
    observer.observe(layer);
    const onMove = (event: PointerEvent) => {
      if (event.pointerType !== "mouse" || event.buttons) return;
      const origin = host.getBoundingClientRect();
      const near = Math.hypot(event.clientX - origin.left, event.clientY - origin.top) <= 100;
      if (near && !nearOpening) play();
      nearOpening = near;
    };
    const onLeave = () => { nearOpening = false; };
    host.addEventListener("pointermove", onMove);
    host.addEventListener("pointerleave", onLeave);
    return () => {
      stop();
      observer.disconnect();
      host.removeEventListener("pointermove", onMove);
      host.removeEventListener("pointerleave", onLeave);
    };
  }, []);
  return <span className="decode-opening" aria-hidden="true" ref={ref} />;
}
