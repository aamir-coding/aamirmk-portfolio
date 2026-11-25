import glyphs from "./art/particles.json";
import engraving from "./art/sparse.webp";

export interface ReliefPlayer { play: (active: boolean) => void; dispose: () => void }

export async function mountRelief(scene: HTMLElement, reflectionOnly: boolean, current: () => boolean): Promise<ReliefPlayer | undefined> {
  const land = scene.querySelector<HTMLImageElement>(".relief-land")!;
  const sparse = scene.querySelector<HTMLImageElement>(".relief-engraving")!;
  const canvas = scene.querySelector("canvas")!;
  const host = scene.querySelector<HTMLElement>(".relief-metal")!;
  const context = canvas.getContext("2d");
  const pointer = { x: -1000, y: -1000, target: 0, strength: 0 };
  let lastFrame = 0;
  let elapsed = 0;
  let frame = 0;
  let disposed = false;
  let active = false;
  let metal: Awaited<ReturnType<typeof import("./liquidRiver").mountRiver>> | undefined;
  const particles = glyphs as [number, number, string, number][];
  function move(event: PointerEvent) {
    if (event.pointerType === "touch") return;
    const rect = scene.getBoundingClientRect();
    pointer.x = (event.clientX - rect.left) * 840 / rect.width;
    pointer.y = (event.clientY - rect.top) * 610 / rect.height;
    pointer.target = 1;
  }
  function leave() { pointer.target = 0; }
  function draw(now: number) {
    if (!context || !active) return;
    if (now - lastFrame >= 42) {
      elapsed += Math.min(now - lastFrame, 84) / 1000;
      lastFrame = now;
      pointer.strength += (pointer.target - pointer.strength) * .28;
      context.clearRect(0, 0, 840, 610);
      context.font = "10px Consolas, monospace";
      context.textBaseline = "top";
      context.fillStyle = "#252423";
      for (const [x, y, mark, alpha] of particles) {
        const dx = x - pointer.x, dy = y - pointer.y;
        const pull = Math.exp(-(dx * dx + dy * dy) / 630) * pointer.strength;
        const light = Math.sin(elapsed * .7 + x * .014 + y * .004);
        context.globalAlpha = alpha / 255 * (.78 + .21 * light);
        context.fillText(mark, x + dx * pull * .21, y + dy * pull * .21 + light * .52);
      }
    }
    frame = requestAnimationFrame(draw);
  }
  sparse.src = engraving;
  await sparse.decode();
  if (!current()) return;
  if (context) {
    sparse.hidden = false;
    canvas.hidden = false;
    land.hidden = true;
  }
  scene.addEventListener("pointermove", move);
  scene.addEventListener("pointerleave", leave);
  if (!reflectionOnly) {
    void import("./liquidRiver").then(async ({ mountRiver }) => {
      if (disposed) return;
      const mounted = await mountRiver(host, () => !disposed);
      if (disposed) mounted?.dispose();
      else { metal = mounted; metal?.setSpeed(active ? .23 : 0); }
    }).catch(() => { if (!disposed) host.replaceChildren(); });
  }
  return {
    play(next) {
      if (active === next) return;
      active = next;
      metal?.setSpeed(active ? .23 : 0);
      cancelAnimationFrame(frame);
      if (active) { lastFrame = performance.now() - 42; draw(lastFrame + 42); }
    },
    dispose() {
      disposed = true;
      active = false;
      cancelAnimationFrame(frame);
      metal?.dispose();
      scene.removeEventListener("pointermove", move);
      scene.removeEventListener("pointerleave", leave);
      sparse.hidden = true;
      canvas.hidden = true;
      land.hidden = false;
    },
  };
}
