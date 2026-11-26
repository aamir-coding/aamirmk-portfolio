import { LiquidMetalShapes, liquidMetalFragmentShader, ShaderMount } from "@paper-design/shaders";

const scale = .86;
const startFrame = 36500;
const pulseDuration = .92;
const releaseDuration = .68;
const reach = .53;
const springRate = 13;
const distanceScale = 1.25;

type Point = { x: number; y: number };
type Drag = { from: Point; target: Point; velocity: Point; at: number; released: number };
const zero = { x: 0, y: 0 };

function dragUniforms(drags: Drag[]) {
  return {
    u_from: drags.map(d => [d.from.x, d.from.y, d.at]),
    u_target: drags.map(d => [d.target.x, d.target.y, d.released]),
    u_velocity: drags.map(d => [d.velocity.x, d.velocity.y]),
  };
}

// Sample the same critically damped spring as the GPU when the pointer changes
// target. Each new segment starts at the displayed position and velocity.
function sampleDrag(drag: Drag, now: number) {
  const dx = drag.from.x - drag.target.x, dy = drag.from.y - drag.target.y;
  const rate = springRate / (1 + distanceScale * Math.hypot(dx, dy));
  const age = Math.max(0, now - drag.at), decay = Math.exp(-rate * age);
  const bx = drag.velocity.x + rate * dx, by = drag.velocity.y + rate * dy;
  return {
    position: { x: drag.target.x + (dx + bx * age) * decay, y: drag.target.y + (dy + by * age) * decay },
    velocity: { x: (drag.velocity.x - rate * bx * age) * decay, y: (drag.velocity.y - rate * by * age) * decay },
  };
}

// Extend only the metaball centres in Paper's pinned shader. Its field blending,
// chrome reflections and RGB dispersion are shared with the unmodified preset.
const fragment = liquidMetalFragmentShader
  .replace("uniform float u_time;", "uniform highp float u_time;")
  .replace("uniform float u_shape;", `
    uniform highp vec3 u_from[5], u_target[5];
    uniform vec2 u_velocity[5];
    uniform highp vec2 u_pulse;
    uniform float u_shape;`)
  .replace("float d = length(shapeUV + traj);", `
    highp float cycles = (u_time - u_pulse.x) / ${pulseDuration};
    float phase = cycles >= 0. && cycles < u_pulse.y ? fract(cycles) : 1.;
    float reunion = smoothstep(.31, .74, phase);
    float scatter = smoothstep(0., .25, phase) * (1. - reunion);
    float gather = reunion * (1. - smoothstep(.76, 1., phase));
    vec2 ring = vec2(cos(fi * 2. * PI / 5.), sin(fi * 2. * PI / 5.));
    traj = mix(traj, ${reach} * ring, scatter) * (1. - .88 * gather);
    traj = clamp(traj, -${reach}, ${reach});
    highp vec3 target = u_target[i];
    float held = target.z < 0. ? 1. : 1. - smoothstep(0., ${releaseDuration}, u_time - target.z);
    if (held > 0.) {
      vec2 delta = u_from[i].xy - target.xy;
      highp float age = max(0., u_time - u_from[i].z);
      float rate = ${springRate.toFixed(1)} / (1. + ${distanceScale} * length(delta));
      vec2 position = target.xy + (delta + (u_velocity[i] + rate * delta) * age) * exp(-rate * age);
      traj = mix(traj, -clamp(position, -${reach}, ${reach}), held);
    }
    float d = max(0., 1.55 * length(shapeUV + traj) - .17);`);

function smoothstep(start: number, end: number, value: number) {
  const t = Math.max(0, Math.min(1, (value - start) / (end - start)));
  return t * t * (3 - 2 * t);
}

const bound = (v: number) => Math.max(-reach, Math.min(reach, v));

export function mountMetaballs(host: HTMLElement) {
  const drags: Drag[] = Array.from({ length: 5 }, () => ({ from: zero, target: zero, velocity: zero, at: 0, released: 0 }));
  const mount = new ShaderMount(host, fragment, {
    u_isImage: false, u_shape: LiquidMetalShapes.metaballs, u_colorBack: [0, 0, 0, 0],
    u_colorTint: [1, 1, 1, 0], u_repetition: 2, u_shiftRed: .32, u_shiftBlue: .36,
    u_contour: .4, u_softness: .13, u_distortion: .07, u_angle: 70,
    u_originX: .5, u_originY: .5, u_worldWidth: 0, u_worldHeight: 0, u_imageAspectRatio: 1,
    u_fit: 1, u_scale: scale, u_rotation: 0, u_offsetX: 0, u_offsetY: 0,
    ...dragUniforms(drags), u_pulse: [0, 0],
  }, { alpha: true }, 0, startFrame, 1, 110000);

  let pulseTime = 0, pulseCount = 0;
  let held = -1, grabOffsetX = 0, grabOffsetY = 0;
  const time = () => mount.getCurrentFrame() / 1000;
  // Paper's five analytic orbits, evaluated only on pickup to find the nearest drop.
  function centre(i: number, now: number) {
    const t = .3 * (now + 2.8);
    const rate = 1.5 + 2 / 3 * Math.sin(i * 12.345);
    const angle = -i * 1.5;
    const a = .4 * Math.sin(t * rate + i * 1.23);
    const b = .4 * Math.cos(t * rate * .7 + i * 2.17);
    const cycles = (now - pulseTime) / pulseDuration;
    const phase = cycles >= 0 && cycles < pulseCount ? cycles % 1 : 1;
    const reunion = smoothstep(.31, .74, phase);
    const scatter = smoothstep(0, .25, phase) * (1 - reunion);
    const gather = reunion * (1 - smoothstep(.76, 1, phase));
    const spread = (orbit: number, axis: number) => -bound(((1 - scatter) * orbit + scatter * reach * axis) * (1 - .88 * gather));
    const cx = spread(Math.cos(angle) * a + Math.cos(angle + 1.57) * b, Math.cos(i * 2 * Math.PI / 5));
    const cy = spread(Math.sin(angle) * a + Math.sin(angle + 1) * b, Math.sin(i * 2 * Math.PI / 5));
    const drag = drags[i]!;
    const blend = drag.released < 0 ? 0 : smoothstep(0, releaseDuration, now - drag.released);
    if (blend === 1) return { x: cx, y: cy };
    const p = sampleDrag(drag, now).position;
    return { x: bound(p.x) * (1 - blend) + cx * blend, y: bound(p.y) * (1 - blend) + cy * blend };
  }

  function point(clientX: number, clientY: number) {
    const rect = host.getBoundingClientRect();
    const unit = 1.3 / (Math.min(rect.width, rect.height) * scale);
    return { x: (clientX - rect.left - rect.width / 2) * unit, y: (clientY - rect.top - rect.height / 2) * unit };
  }

  function scatter(sendCount = 0) {
    const now = time();
    if (now < pulseTime + pulseCount * pulseDuration) {
      if (!sendCount) return;
      pulseCount += sendCount;
    } else {
      pulseTime = now;
      pulseCount = sendCount || 1;
    }
    mount.setUniforms({ u_pulse: [pulseTime, pulseCount] });
  }

  function retarget(target: Point | null) {
    if (held < 0) return;
    const now = time();
    const { position, velocity } = sampleDrag(drags[held]!, now);
    drags[held] = { from: position, target: target ?? position, velocity, at: now, released: target ? -1 : now };
    mount.setUniforms(dragUniforms(drags));
  }

  return {
    mount,
    grab(clientX: number, clientY: number) {
      const p = point(clientX, clientY), now = time();
      const centres = Array.from({ length: 5 }, (_, i) => centre(i, now));
      const distances = centres.map(c => Math.hypot(p.x - c.x, p.y - c.y));
      held = distances.indexOf(Math.min(...distances));
      const selected = centres[held]!;
      grabOffsetX = selected.x - p.x;
      grabOffsetY = selected.y - p.y;
      drags[held] = { from: selected, target: selected, velocity: zero, at: now, released: -1 };
      mount.setUniforms(dragUniforms(drags));
    },
    move(clientX: number, clientY: number) {
      const p = point(clientX, clientY);
      retarget({ x: bound(p.x + grabOffsetX), y: bound(p.y + grabOffsetY) });
    },
    release() {
      retarget(null);
      held = -1;
    },
    scatter: () => scatter(),
    scatterOnSend: (count: number) => scatter(count),
  };
}
