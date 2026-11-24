import { useEffect, useRef } from "react";
import terrain from "./art/terrain.webp";
import reflection from "./art/silver.webp";
import type { ReliefPlayer } from "./fieldMotion";

interface ArtProps {
  paused: boolean;
  reflectionOnly: boolean;
  onPause: () => void;
}

export function HeroArt({ paused, reflectionOnly, onPause }: ArtProps) {
  const scene = useRef<HTMLDivElement>(null);
  const player = useRef<ReliefPlayer | null>(null);
  const pausedRef = useRef(paused);

  const syncPlayback = useRef<() => void>(() => {});
  useEffect(() => {
    pausedRef.current = paused;
    syncPlayback.current();
  }, [paused]);

  useEffect(() => {
    const element = scene.current;
    if (!element || !window.matchMedia || !window.IntersectionObserver) return;
    const media = matchMedia("(prefers-reduced-motion: no-preference) and (forced-colors: none)");
    let disposed = false;
    let visible = false;
    let pending = false;
    let failed = false;
    const sync = () => {
      const active = visible && media.matches && !document.hidden;
      if (player.current) {
        player.current.play(active && !pausedRef.current);
        return;
      }
      if (disposed || pending || failed || !active || pausedRef.current || document.readyState !== "complete") return;
      pending = true;
      void import("./fieldMotion").then(async ({ mountRelief }) => {
        if (disposed || !media.matches) return;
        const mounted = await mountRelief(element, reflectionOnly, () => !disposed);
        if (!mounted) return;
        if (disposed) mounted.dispose();
        else {
          player.current = mounted;
          mounted.play(visible && media.matches && !document.hidden && !pausedRef.current);
        }
      }).catch(() => { failed = true; }).finally(() => { pending = false; });
    };
    const observer = new IntersectionObserver(([entry]) => { visible = entry?.isIntersecting ?? false; sync(); });
    observer.observe(element);
    media.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    window.addEventListener("load", sync);
    // A pause before the first load can be lifted without remounting the scene.
    syncPlayback.current = sync;
    return () => {
      disposed = true;
      observer.disconnect();
      media.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
      window.removeEventListener("load", sync);
      syncPlayback.current = () => {};
      player.current?.dispose();
      player.current = null;
    };
  }, [reflectionOnly]);

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
    <button type="button" className="relief-pause" aria-pressed={paused} onClick={onPause}>
      {paused ? "Resume artwork" : "Pause artwork"}
    </button>
  </div>;
}
