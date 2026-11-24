import { useCallback, useEffect, useRef, useState } from "react";

export type Artwork = "metal" | "reflection" | "still";
interface Preferences { artwork: Artwork; sound: boolean }
function initialPreferences(): Preferences {
  const defaults: Preferences = { artwork: "metal", sound: false };
  try {
    const saved = JSON.parse(localStorage.getItem("amk_art_preferences") ?? "{}");
    // Retain the previous pause and river choices for returning visitors.
    const artwork = saved.artwork === "still" || saved.paused === true ? "still"
      : saved.artwork === "reflection" || saved.reflectionOnly === true ? "reflection" : "metal";
    return { artwork, sound: saved.sound === true };
  } catch { return defaults; }
}

export function useArtPreferences() {
  const [preferences, setPreferences] = useState(initialPreferences);
  const audio = useRef<AudioContext | null>(null);
  useEffect(() => {
    try { localStorage.setItem("amk_art_preferences", JSON.stringify(preferences)); } catch { /* In-memory preferences still work. */ }
  }, [preferences]);
  useEffect(() => () => { void audio.current?.close().catch(() => {}); audio.current = null; }, []);
  const set = <K extends keyof Preferences>(key: K, value: Preferences[K]) => setPreferences(old => ({ ...old, [key]: value }));
  const cue = useCallback((kind: "send" | "evidence") => {
    if (!preferences.sound || typeof AudioContext === "undefined") return;
    try {
      const context = audio.current ??= new AudioContext();
      void context.resume().then(() => {
        const voice = context.createOscillator();
        const gain = context.createGain();
        const start = context.currentTime;
        voice.type = kind === "send" ? "triangle" : "sine";
        voice.frequency.setValueAtTime(kind === "send" ? 570 : 860, start);
        voice.frequency.exponentialRampToValueAtTime(kind === "send" ? 360 : 690, start + .06);
        gain.gain.setValueAtTime(.001, start);
        gain.gain.exponentialRampToValueAtTime(.05, start + .004);
        gain.gain.exponentialRampToValueAtTime(.0001, start + .085);
        voice.connect(gain).connect(context.destination);
        voice.start(start);
        voice.stop(start + .09);
      }).catch(() => {});
    } catch { /* Audio is an optional enhancement. */ }
  }, [preferences.sound]);
  return { preferences, set, cue };
}
