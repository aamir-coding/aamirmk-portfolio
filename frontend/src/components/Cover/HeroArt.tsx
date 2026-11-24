import { useEffect, useRef } from "react";
import terrain from "./art/terrain.webp";
import reflection from "./art/silver.webp";
import type { ReliefPlayer } from "./fieldMotion";
import type { Artwork } from "../../hooks/useArtPreferences";

export function HeroArt({ artwork }: { artwork: Artwork }) {
  const scene = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = scene.current;
    if (!element || artwork === "still" || !window.matchMedia || !window.IntersectionObserver) return;
    let player: ReliefPlayer | undefined;
    const media = matchMedia("(prefers-reduced-motion: no-preference) and (forced-colors: none)");
    let disposed = false;
    let visible = false;
    let pending = false;
    let failed = false;
    const sync = () => {
      const active = visible && media.matches && !document.hidden;
      if (player) {
        player.play(active);
        return;
      }
      if (disposed || pending || failed || !active || document.readyState !== "complete") return;
      pending = true;
      void import("./fieldMotion").then(async ({ mountRelief }) => {
        if (disposed || !media.matches) return;
        const mounted = await mountRelief(element, artwork === "reflection", () => !disposed);
        if (!mounted) return;
        if (disposed) mounted.dispose();
        else {
          player = mounted;
          mounted.play(visible && media.matches && !document.hidden);
        }
      }).catch(() => { failed = true; }).finally(() => { pending = false; });
    };
    const observer = new IntersectionObserver(([entry]) => { visible = entry?.isIntersecting ?? false; sync(); });
    observer.observe(element);
    media.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    window.addEventListener("load", sync);
    return () => {
      disposed = true;
      observer.disconnect();
      media.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
      window.removeEventListener("load", sync);
      player?.dispose();
    };
  }, [artwork]);

  return <div className="relief">
    <div className="relief-scene" aria-hidden="true" ref={scene}>
      <img className="relief-land" src={terrain} width="840" height="610" alt="" />
      <img className="relief-engraving" hidden alt="" />
      <canvas className="relief-type" width="840" height="610" hidden />
      <div className="relief-river">
        <img src={reflection} width="452" height="232" alt="" />
        <div className="relief-metal" />
      </div>
    </div>
  </div>;
}
