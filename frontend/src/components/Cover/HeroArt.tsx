import { useEffect, useRef, useState, type RefObject } from "react";
import desktop from "./art/field-desktop.webp";
import mobile from "./art/field-mobile.webp";
import tablet from "./art/field-tablet.webp";
import type { LandscapeMotion, MotionControl } from "./fieldMotion";

export function HeroArt({ pausedPreference }: { pausedPreference: RefObject<boolean> }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const player = useRef<LandscapeMotion>(null);
  const toggleMotion = useRef<() => void>(null);
  const [control, setControl] = useState<MotionControl>("unavailable");

  useEffect(() => {
    const canvas = canvasRef.current;
    const hero = canvas?.closest<HTMLElement>(".portfolio-cover");
    if (!canvas || !hero || !window.IntersectionObserver || !window.matchMedia) return;
    const motion = window.matchMedia("(prefers-reduced-motion: no-preference) and (forced-colors: none)");
    let loaded = false;
    let disposed = false;
    let cancelPending: (() => void) | undefined;

    function schedule() {
      if (document.readyState !== "complete" || loaded || cancelPending || !motion.matches || pausedPreference.current) return;
      const enhance = () => {
        cancelPending = undefined;
        if (disposed || !motion.matches || pausedPreference.current) return;
        loaded = true;
        // The poster and composer paint before the optional canvas module starts.
        void import("./fieldMotion").then(({ mountLandscape }) => {
          if (!disposed && hero && canvas) {
            player.current = mountLandscape(hero, canvas, motion, pausedPreference.current, setControl) ?? null;
            if (!player.current) setControl("unavailable");
          }
        }).catch(() => { if (!disposed) setControl("unavailable"); });
      };
      if (typeof window.requestIdleCallback === "function") {
        const id = window.requestIdleCallback(enhance, { timeout: 750 });
        cancelPending = () => window.cancelIdleCallback(id);
      } else {
        const id = window.setTimeout(enhance, 0);
        cancelPending = () => window.clearTimeout(id);
      }
    }

    function syncPreference() {
      if (!player.current) setControl(motion.matches && pausedPreference.current ? "paused" : "unavailable");
      schedule();
    }

    toggleMotion.current = () => {
      pausedPreference.current = !pausedPreference.current;
      if (player.current) player.current.setPaused(pausedPreference.current);
      else {
        setControl(pausedPreference.current ? "paused" : "playing");
        schedule();
      }
    };
    window.addEventListener("load", syncPreference);
    motion.addEventListener("change", syncPreference);
    syncPreference();
    return () => {
      disposed = true;
      cancelPending?.();
      window.removeEventListener("load", syncPreference);
      motion.removeEventListener("change", syncPreference);
      player.current?.dispose();
      player.current = null;
      toggleMotion.current = null;
    };
  }, [pausedPreference]);

  return (
    <>
      <div className="portfolio-hero-art" aria-hidden="true">
        <div className="portfolio-art-scene">
          <canvas ref={canvasRef} />
          <picture>
            <source media="(max-width: 700px)" srcSet={mobile} width={610} height={444} />
            <source media="(max-width: 1120px)" srcSet={tablet} width={1180} height={690} />
            <img
              src={desktop}
              alt=""
              width={1180}
              height={690}
              decoding="async"
              fetchPriority="high"
              onError={event => { event.currentTarget.hidden = true; }}
              onLoad={event => { event.currentTarget.hidden = false; }}
            />
          </picture>
        </div>
      </div>
      {control !== "unavailable" && (
        <button className="portfolio-art-control" type="button" onClick={() => toggleMotion.current?.()}>
          {control === "paused" ? "Resume motion" : "Pause motion"}
        </button>
      )}
    </>
  );
}
