import { memo, useEffect, useRef } from "react";
import etchedEdge from "./etch.webp";
import poster from "./ribbon.webp";
import water from "../Cover/art/silver.webp";

export interface RibbonSend {
  at: number;
  river?: DOMRect;
}
type Stage = "waiting" | "writing" | "settled" | "stopped";
type Player = ReturnType<typeof import("./ribbonRenderer").mountRibbon>;

export const ConversationRibbon = memo(function ConversationRibbon({ send, stage, graphite, live }: {
  send: RibbonSend | null; stage: Stage; graphite: boolean; live: boolean;
}) {
  const host = useRef<HTMLDivElement>(null);
  const player = useRef<Player>(undefined);
  const dark = useRef(graphite);
  const sweep = useRef({ start: 0, distance: 0, duration: 0 });
  useEffect(() => {
    dark.current = graphite;
    player.current?.theme(graphite);
  }, [graphite]);
  useEffect(() => {
    const now = performance.now();
    const recentSend = send && now - send.at < 900;
    const duration = stage === "waiting" ? 820 : 460;
    const distance = !send || stage === "stopped" ? 0 : stage === "writing" ? .48 : recentSend ? 1.4 : 0;
    sweep.current = { start: now, distance, duration };
    player.current?.stop();
    if (distance && !document.hidden) player.current?.sweep(distance, duration);
  }, [send, stage]);
  useEffect(() => {
    const element = host.current;
    if (!element || !live || !window.matchMedia || !window.IntersectionObserver) return;
    const media = matchMedia("(prefers-reduced-motion: no-preference) and (forced-colors: none)");
    let visible = false, disposed = false, pending = false, failed = false;
    const container = element;
    function onContextLost() { failed = true; clear(); }
    function clear() {
      container.firstChild?.removeEventListener("webglcontextlost", onContextLost);
      player.current?.dispose();
      player.current = undefined;
      container.replaceChildren();
    }
    function sync() {
      if (!media.matches || !visible || document.hidden) { clear(); return; }
      if (pending || failed || player.current) return;
      pending = true;
      void import("./ribbonRenderer").then(({ mountRibbon }) => {
        if (disposed || !media.matches || !visible || document.hidden) return;
        const canvas = document.createElement("canvas");
        player.current = mountRibbon(canvas);
        if (!player.current) { failed = true; return; }
        container.append(canvas);
        canvas.addEventListener("webglcontextlost", onContextLost, { once: true });
        player.current.theme(dark.current);
        const { start, distance, duration } = sweep.current;
        const remaining = duration - (performance.now() - start);
        if (remaining > 0 && distance) player.current.sweep(distance * remaining / duration, remaining);
      }).catch(() => { failed = true; }).finally(() => { pending = false; });
    }
    const observer = new IntersectionObserver(([entry]) => { visible = Boolean(entry?.isIntersecting); sync(); });
    observer.observe(element);
    const resize = new ResizeObserver(() => player.current?.theme(dark.current));
    resize.observe(element);
    media.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    return () => {
      disposed = true;
      observer.disconnect();
      resize.disconnect();
      media.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
      clear();
    };
  }, [live]);
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
  return <div className="conversation-ribbon" aria-hidden="true">
    <div className="ribbon-surface" ref={host} style={{ backgroundImage: `url(${poster})` }} />
    <img src={etchedEdge} alt="" width="320" height="400" />
  </div>;
});
