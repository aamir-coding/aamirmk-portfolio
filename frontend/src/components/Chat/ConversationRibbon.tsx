import { memo, useEffect, useRef } from "react";
import etchedEdge from "./etch.webp";
import compactEdge from "./etch-compact.webp";
import poster from "./ribbon.webp";
import mask from "./ribbon-texture.png";
import type { ShaderMount } from "@paper-design/shaders";
import water from "../Cover/art/silver.webp";

export interface RibbonSend {
  at: number;
  river?: DOMRect;
}
type Stage = "waiting" | "writing" | "settled" | "stopped";

export const ConversationRibbon = memo(function ConversationRibbon({ send, stage, live }: {
  send: RibbonSend | null; stage: Stage; live: boolean;
}) {
  const host = useRef<HTMLDivElement>(null);
  const player = useRef<ShaderMount | undefined>(undefined);
  const flowSpeed = stage === "waiting" ? .4 : stage === "writing" ? .3 : .23;
  const speed = useRef(flowSpeed);
  useEffect(() => {
    speed.current = flowSpeed;
    player.current?.setSpeed(flowSpeed);
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
      player.current?.canvasElement.removeEventListener("webglcontextlost", onContextLost);
      player.current?.dispose();
      player.current = undefined;
      container.replaceChildren();
    }
    function sync() {
      if (!media.matches || !visible || document.hidden) { clear(); return; }
      if (pending || failed || player.current) return;
      pending = true;
      void import("../Cover/liquidRiver").then(async ({ mountLiquidMetal }) => {
        if (!active()) return;
        const mount = await mountLiquidMetal(container, mask, active);
        if (!mount) return;
        if (!active()) { mount.dispose(); return; }
        player.current = mount;
        mount.canvasElement.addEventListener("webglcontextlost", onContextLost, { once: true });
        mount.setSpeed(speed.current);
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
    <picture>
      <source media="(max-width: 700px)" srcSet={compactEdge} />
      <img src={etchedEdge} alt="" width="720" height="900" />
    </picture>
  </div>;
});
