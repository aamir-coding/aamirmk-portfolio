import landscapeSource from "./art/field-motion-source.webp";

const marks = " .:;+=o*#%@";
const glyphFont = '12px Consolas, "Courier New", monospace';
const loopDuration = 14_000;
const pointerRadius = 64;

export type MotionControl = "unavailable" | "playing" | "paused";

export interface LandscapeMotion {
  setPaused: (paused: boolean) => void;
  dispose: () => void;
}

interface Glyph {
  x: number;
  y: number;
  index: number;
  value: number;
  alpha: number;
  color: string;
  front: number;
  seed: number;
}

interface GlyphField {
  width: number;
  height: number;
  stepX: number;
  stepY: number;
  points: Glyph[];
}

function makeGlyphs(image: HTMLImageElement, mobile: boolean): GlyphField | undefined {
  const width = mobile ? 610 : 1180;
  const height = mobile ? 444 : 690;
  const stepX = mobile ? 9 : 10;
  const stepY = 12;
  const columns = Math.floor(width / stepX);
  const rows = Math.floor(height / stepY);
  const sample = document.createElement("canvas");
  sample.width = columns;
  sample.height = rows;
  const context = sample.getContext("2d", { willReadFrequently: true });
  if (!context) return;
  const cropStart = mobile ? image.width * .34 : 0;
  context.drawImage(image, cropStart, 0, image.width - cropStart, image.height, 0, 0, columns, rows);
  const values = context.getImageData(0, 0, columns, rows).data;
  const points: Glyph[] = [];
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < columns; col++) {
      const value = (values[(row * columns + col) * 4] ?? 0) / 255;
      if (value < .09) continue;
      const x = col * stepX + 1;
      const y = row * stepY + 1;
      const color = value > .82 ? "#dcfff1" : value > .61 ? "#e3f5ff" : value > .32 ? "#a8d9db" : "#759db9";
      points.push({
        x,
        y,
        color,
        value,
        index: Math.min(marks.length - 1, 1 + Math.floor(value * 10)),
        alpha: Math.min(.94, Math.round((.12 + value * .92) * 16) / 16),
        front: .84 * x / width + .16 * y / height,
        seed: (row * 11 + col * 17) % 31 / 31,
      });
    }
  }
  return { width, height, stepX, stepY, points };
}

function resizeContext(context: CanvasRenderingContext2D, field: GlyphField) {
  context.canvas.width = field.width;
  context.canvas.height = field.height;
  context.font = glyphFont;
  context.textBaseline = "top";
}

export function mountLandscape(
  hero: HTMLElement,
  canvas: HTMLCanvasElement,
  motion: MediaQueryList,
  initiallyPaused: boolean,
  setControl: (control: MotionControl) => void,
): LandscapeMotion | undefined {
  const output = canvas.getContext("2d");
  const still = document.createElement("canvas").getContext("2d");
  if (!output || !still) return;
  const context = output;
  const base = still;
  const mobile = matchMedia("(max-width: 700px)");
  const image = new Image();
  const changed: { point: Glyph; crest: number; moveX: number; moveY: number }[] = [];
  const target = { x: 0, y: 0, active: false };
  const magnet = { x: 0, y: 0, strength: 0 };
  let field: GlyphField | undefined;
  let preparedMobile: boolean | undefined;
  let visible = false;
  let paused = initiallyPaused;
  let frame = 0;
  let lastPaint = 0;
  let nextPaint = 0;
  let elapsed = 1400;

  function followPointer(grid: GlyphField, delta: number) {
    const previousStrength = magnet.strength;
    const targetStrength = target.active ? 1 : 0;
    const response = 1 - Math.exp(-delta / (target.active ? 34 : 56));
    magnet.strength += (targetStrength - magnet.strength) * response;
    if (target.active) {
      const positionResponse = previousStrength < .01 ? 1 : 1 - Math.exp(-delta / 15);
      magnet.x += (target.x - magnet.x) * positionResponse;
      magnet.y += (target.y - magnet.y) * positionResponse;
    }
    if (magnet.strength < .01) return null;

    const rect = canvas.getBoundingClientRect();
    const scale = Math.max(rect.width / grid.width, rect.height / grid.height);
    const alignment = parseFloat(getComputedStyle(canvas).getPropertyValue("--landscape-position")) / 100;
    const offset = (rect.width - grid.width * scale) * alignment;
    return {
      x: (magnet.x - rect.left - offset) / scale,
      y: (magnet.y - rect.bottom) / scale + grid.height,
      radiusSquared: (pointerRadius / scale) ** 2,
    };
  }

  function paint(grid: GlyphField, delta: number) {
    const pointer = followPointer(grid, delta);
    const phase = (elapsed % loopDuration) / loopDuration;
    // Copy the still once, then redraw only glyphs touched by the sweep or pointer.
    context.globalAlpha = 1;
    context.clearRect(0, 0, grid.width, grid.height);
    context.drawImage(base.canvas, 0, 0);
    changed.length = 0;
    for (const point of grid.points) {
      const progress = (point.front - phase + 1) % 1;
      const distanceFromFront = Math.min(progress, 1 - progress);
      const crest = distanceFromFront < .16 && point.value > .16
        ? (1 - distanceFromFront / .16) ** 2 : 0;
      let moveX = 0;
      let moveY = 0;
      if (pointer) {
        const dx = pointer.x - point.x;
        const dy = pointer.y - point.y;
        const falloff = 1 - (dx * dx + dy * dy) / pointer.radiusSquared;
        if (falloff > 0) {
          // The pull and its slope fade to zero at the edge.
          const pull = magnet.strength * falloff ** 3 * (.49 + .17 * point.seed);
          moveX = dx * pull;
          moveY = dy * pull;
        }
      }
      if (crest < .025 && Math.abs(moveX) + Math.abs(moveY) < .18) continue;
      context.clearRect(point.x, point.y, grid.stepX, grid.stepY);
      changed.push({ point, crest, moveX, moveY });
    }
    for (const { point, crest, moveX, moveY } of changed) {
      const glint = crest > .26 && Math.sin(phase * 8 * Math.PI + point.seed * 6.28) > -.2;
      const index = Math.min(marks.length - 1, point.index + Number(glint));
      context.fillStyle = crest > .37 ? "#d3eef8" : point.color;
      context.globalAlpha = Math.min(.96, point.alpha + crest * .40);
      context.fillText(marks.charAt(index), point.x + moveX, point.y + moveY - crest * 2);
    }
  }

  function tick(now: number) {
    if (!field) return;
    const interval = target.active || magnet.strength > .03 ? 1000 / 30 : 1000 / 24;
    if (now + .7 >= nextPaint) {
      const delta = Math.min(now - lastPaint, 85);
      elapsed += delta;
      lastPaint = now;
      nextPaint = Math.max(nextPaint + interval, now + interval / 2);
      paint(field, delta);
      if (canvas.dataset.active !== "true") canvas.dataset.active = "true";
    }
    frame = requestAnimationFrame(tick);
  }

  function sync() {
    const canPaint = motion.matches && !paused && visible && !document.hidden;
    if (canPaint) {
      if (image.naturalWidth && preparedMobile !== mobile.matches) prepare();
      else if (!image.src) image.src = landscapeSource;
    }
    const available = (Boolean(field) || paused) && motion.matches;
    const enabled = available && !paused;
    if (!motion.matches) setControl("unavailable");
    else if (available) setControl(paused ? "paused" : "playing");
    hero.dataset.motion = enabled ? "on" : "off";
    if (canPaint && field) {
      if (!frame) {
        lastPaint = performance.now();
        nextPaint = lastPaint;
        frame = requestAnimationFrame(tick);
      }
    } else {
      cancelAnimationFrame(frame);
      frame = 0;
      magnet.strength = 0;
      canvas.dataset.active = "false";
    }
  }

  function prepare() {
    if (!image.naturalWidth) return;
    const next = makeGlyphs(image, mobile.matches);
    if (!next) return;
    resizeContext(base, next);
    for (const point of next.points) {
      base.globalAlpha = point.alpha;
      base.fillStyle = point.color;
      base.fillText(marks.charAt(point.index), point.x, point.y);
    }
    resizeContext(context, next);
    field = next;
    preparedMobile = mobile.matches;
    canvas.dataset.active = "false";
  }

  function trackPointer(event: PointerEvent) {
    if (event.pointerType === "touch") return;
    target.active = true;
    target.x = event.clientX;
    target.y = event.clientY;
  }

  function releasePointer(event: PointerEvent) {
    if (event.pointerType !== "touch") target.active = false;
  }

  const lifetime = new AbortController();
  const listener = { signal: lifetime.signal };
  const passive = { ...listener, passive: true };
  const observer = new IntersectionObserver(([entry]) => {
    if (lifetime.signal.aborted) return;
    visible = Boolean(entry?.isIntersecting);
    sync();
  });
  image.onload = sync;
  image.onerror = () => { if (!paused) setControl("unavailable"); };
  observer.observe(canvas);
  hero.addEventListener("pointerenter", trackPointer, passive);
  hero.addEventListener("pointermove", trackPointer, passive);
  hero.addEventListener("pointerleave", releasePointer, passive);
  hero.addEventListener("pointercancel", releasePointer, passive);
  document.addEventListener("visibilitychange", sync, listener);
  motion.addEventListener("change", sync, listener);
  mobile.addEventListener("change", sync, listener);

  return {
    setPaused(next) {
      paused = next;
      sync();
    },
    dispose() {
      lifetime.abort();
      observer.disconnect();
      cancelAnimationFrame(frame);
      image.onload = null;
      image.onerror = null;
      delete canvas.dataset.active;
      delete hero.dataset.motion;
    },
  };
}
