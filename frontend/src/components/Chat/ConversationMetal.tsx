import { memo, useEffect, useRef, useState } from "react";
import poster from "./metaballs.webp";
import type { mountMetaballs } from "./metaballShader";
import water from "../Cover/art/silver.webp";

export interface MetalSend {
  count: number;
  at: number;
  river?: DOMRect;
}
type Stage = "waiting" | "writing" | "settled" | "stopped";

export const ConversationMetal = memo(function ConversationMetal({ send, stage, live }: {
  send: MetalSend | null; stage: Stage; live: boolean;
}) {
  const host = useRef<HTMLSpanElement>(null);
  const player = useRef<ReturnType<typeof mountMetaballs> | undefined>(undefined);
  const [ready, setReady] = useState(false);
  const consumedSends = useRef(0);
  const drag = useRef<{ id: number; x: number; y: number } | null>(null);
  const dragged = useRef(false);
  const flowSpeed = stage === "waiting" ? .78 : stage === "writing" ? .63 : .52;
  const speed = useRef(flowSpeed);
  useEffect(() => {
    speed.current = flowSpeed;
    player.current?.mount.setSpeed(flowSpeed);
  }, [flowSpeed]);
  useEffect(() => {
    const element = host.current;
    if (!element || !live || !window.matchMedia || !window.IntersectionObserver) return;
    const media = matchMedia("(prefers-reduced-motion: no-preference) and (forced-colors: none)");
    let visible = false, disposed = false, pending = false, failed = false;
    const container = element;
    const active = () => !disposed && visible && media.matches && !document.hidden;
    function onContextLost() { failed = true; clear(); }
    function clear() {
      player.current?.mount.canvasElement.removeEventListener("webglcontextlost", onContextLost);
      player.current?.mount.dispose();
      player.current = undefined;
      drag.current = null;
      setReady(false);
      container.replaceChildren();
    }
    function sync() {
      if (!media.matches || !visible || document.hidden) { clear(); return; }
      if (pending || failed || player.current) return;
      pending = true;
      void import("./metaballShader").then(({ mountMetaballs }) => {
        if (!active()) return;
        const field = mountMetaballs(container);
        player.current = field;
        field.mount.canvasElement.addEventListener("webglcontextlost", onContextLost, { once: true });
        field.mount.setSpeed(speed.current);
        setReady(true);
      }).catch(() => { failed = true; if (!disposed) clear(); }).finally(() => { pending = false; });
    }
    const observer = new IntersectionObserver(([entry]) => { visible = Boolean(entry?.isIntersecting); sync(); });
    observer.observe(element);
    media.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    return () => {
      disposed = true;
      observer.disconnect();
      media.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
      clear();
    };
  }, [live]);
  useEffect(() => {
    if (!send || consumedSends.current >= send.count) return;
    if (live && !document.hidden && window.matchMedia?.("(prefers-reduced-motion: no-preference) and (forced-colors: none)").matches) {
      if (!ready || !player.current) return;
      player.current.scatterOnSend(send.count - consumedSends.current);
    }
    consumedSends.current = send.count;
  }, [live, ready, send]);
  useEffect(() => {
    const river = send?.river, target = host.current;
    if (!live || !river || !target || performance.now() - send.at > 350 || !target.animate ||
        !window.matchMedia?.("(prefers-reduced-motion: no-preference) and (forced-colors: none)").matches) return;
    const dest = target.getBoundingClientRect();
    const image = new Image();
    image.className = "river-handoff";
    image.src = water;
    image.alt = "";
    Object.assign(image.style, { left: river.x + "px", top: river.y + "px", width: river.width + "px", height: river.height + "px" });
    document.body.append(image);
    const move = image.animate([
      { opacity: .75, transform: "none" },
      { opacity: 0, transform: `translate(${dest.x + dest.width/2 - river.x}px, ${dest.y + dest.height/2 - river.y}px) scale(.12)` },
    ], { duration: 300, easing: "ease-out" });
    move.onfinish = () => image.remove();
    return () => { move.cancel(); image.remove(); };
  }, [send, live]);
  const release = (pointerId: number) => {
    if (drag.current?.id !== pointerId) return;
    drag.current = null;
    if (dragged.current) player.current?.release();
  };
  return <button type="button" className="conversation-metal" disabled={!ready}
    aria-hidden={!ready || undefined} aria-label="Scatter the liquid metal drops"
    title={ready ? "Drag a drop, or tap to scatter" : undefined}
    onPointerDown={event => {
      if (drag.current || !event.isPrimary || event.button !== 0 || !player.current) return;
      drag.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
      dragged.current = false;
      event.currentTarget.setPointerCapture(event.pointerId);
    }}
    onPointerMove={event => {
      const start = drag.current;
      if (!start || start.id !== event.pointerId) return;
      if (!dragged.current) {
        if (Math.hypot(event.clientX - start.x, event.clientY - start.y) <= 3) return;
        player.current?.grab(start.x, start.y);
        dragged.current = true;
      }
      player.current?.move(event.clientX, event.clientY);
    }}
    onPointerUp={event => release(event.pointerId)}
    onPointerCancel={event => release(event.pointerId)}
    onLostPointerCapture={event => release(event.pointerId)}
    onClick={event => { if (event.detail === 0 || !dragged.current) player.current?.scatter(); }}>
    <span className="metaball-surface" aria-hidden="true" ref={host} style={{ backgroundImage: `url(${poster})` }} />
  </button>;
});
