import { useCallback, useEffect, useRef, useState } from "react";

export type Artwork = "metal" | "reflection" | "still";
interface Preferences { artwork: Artwork; sound: boolean }
function initialPreferences(): Preferences {
  const defaults: Preferences = { artwork: "metal", sound: true };
  try {
    const saved = JSON.parse(localStorage.getItem("amk_art_preferences") ?? "{}");
    // Retain the previous pause and river choices for returning visitors.
    const artwork = saved.artwork === "still" || saved.paused === true ? "still"
      : saved.artwork === "reflection" || saved.reflectionOnly === true ? "reflection" : "metal";
    return { artwork, sound: typeof saved.sound === "boolean" ? saved.sound : defaults.sound };
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
  const cue = useCallback((kind: "send" | "evidence" | "ready") => {
    if (!preferences.sound || document.hidden || typeof AudioContext === "undefined") return;
    try {
      const context = audio.current ??= new AudioContext();
      void context.resume().then(() => {
        const start = context.currentTime;
        if (kind === "evidence") {
          const length = Math.ceil(context.sampleRate * .09);
          const buffer = context.createBuffer(1, length, context.sampleRate);
          const samples = buffer.getChannelData(0);
          for (let i = 0; i < length; i++) samples[i] = (Math.random() * 2 - 1) * Math.sin(Math.PI * i / length) ** 2;
          const brush = context.createBufferSource(), filter = context.createBiquadFilter(), gain = context.createGain();
          brush.buffer = buffer;
          filter.type = "bandpass";
          filter.frequency.value = 1650;
          gain.gain.value = .09;
          brush.connect(filter).connect(gain).connect(context.destination);
          brush.start();
          return;
        }
        const tones = kind === "send" ? [[680,.07,.045,0],[1315,.05,.012,0]] as const
          : [[494,.12,.025,0],[659,.15,.017,.045]] as const;
        for (const [frequency, duration, level, delay] of tones) {
          const voice = context.createOscillator(), gain = context.createGain();
          const t = start + delay;
          voice.frequency.value = frequency;
          gain.gain.setValueAtTime(.0001, t);
          gain.gain.exponentialRampToValueAtTime(level, t + .004);
          gain.gain.exponentialRampToValueAtTime(.0001, t + duration);
          voice.connect(gain).connect(context.destination);
          voice.start(t);
          voice.stop(t + duration + .01);
        }
      }).catch(() => {});
    } catch { /* Audio is an optional enhancement. */ }
  }, [preferences.sound]);
  return { preferences, set, cue };
}
