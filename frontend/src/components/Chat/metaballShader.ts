import { LiquidMetalShapes, liquidMetalFragmentShader, ShaderMount } from "@paper-design/shaders";

const scale = .86;
const startFrame = 36500;
const pulseDuration = .92;
const releaseDuration = .34;
const reach = .53;

// Extend only the metaball centres in Paper's pinned shader. Its field blending,
// chrome reflections and RGB dispersion are shared with the unmodified preset.
const fragment = liquidMetalFragmentShader
  .replace("uniform float u_shape;", "uniform vec4 u_grab; uniform float u_pulse; uniform float u_shape;")
  .replace("float d = length(shapeUV + traj);", `
    float phase = clamp((u_time - u_pulse) / ${pulseDuration}, 0., 1.);
    float scatter = smoothstep(0., .25, phase) * (1. - smoothstep(.35, .65, phase));
    float gather = smoothstep(.35, .65, phase) * (1. - smoothstep(.7, 1., phase));
    vec2 ring = vec2(cos(fi * 2. * PI / 5.), sin(fi * 2. * PI / 5.));
    traj = mix(traj, ${reach} * ring, scatter) * (1. - .88 * gather);
    traj = clamp(traj, -${reach}, ${reach});
    if (abs(fi - u_grab.z) < .25) {
      float held = u_grab.w < 0. ? 1. : 1. - smoothstep(0., ${releaseDuration}, u_time - u_grab.w);
      traj = mix(traj, -u_grab.xy, held);
    }
    float d = max(0., 1.55 * length(shapeUV + traj) - .17);`);

function smoothstep(start: number, end: number, value: number) {
  const t = Math.max(0, Math.min(1, (value - start) / (end - start)));
  return t * t * (3 - 2 * t);
}

const bound = (v: number) => Math.max(-reach, Math.min(reach, v));

export function mountMetaballs(host: HTMLElement) {
  const mount = new ShaderMount(host, fragment, {
    u_isImage: false, u_shape: LiquidMetalShapes.metaballs, u_colorBack: [0, 0, 0, 0],
    u_colorTint: [1, 1, 1, 0], u_repetition: 2, u_shiftRed: .32, u_shiftBlue: .36,
    u_contour: .4, u_softness: .13, u_distortion: .07, u_angle: 70,
    u_originX: .5, u_originY: .5, u_worldWidth: 0, u_worldHeight: 0, u_imageAspectRatio: 1,
    u_fit: 1, u_scale: scale, u_rotation: 0, u_offsetX: 0, u_offsetY: 0,
    u_grab: [0, 0, -1, -1], u_pulse: -10,
  }, { alpha: true }, 0, startFrame, 1, 110000);

  let pulseTime = -10;
  let held = -1, releaseTime = -1;
  let x = 0, y = 0, grabOffsetX = 0, grabOffsetY = 0;
  const time = () => mount.getCurrentFrame() / 1000;
  // Paper's five analytic orbits, evaluated only on pickup to find the nearest drop.
  function centre(i: number, now: number) {
    const t = .3 * (now + 2.8);
    const rate = 1.5 + 2 / 3 * Math.sin(i * 12.345);
    const angle = -i * 1.5;
    const a = .4 * Math.sin(t * rate + i * 1.23);
    const b = .4 * Math.cos(t * rate * .7 + i * 2.17);
    const phase = (now - pulseTime) / pulseDuration;
    const scatter = smoothstep(0, .25, phase) * (1 - smoothstep(.35, .65, phase));
    const gather = smoothstep(.35, .65, phase) * (1 - smoothstep(.7, 1, phase));
    const spread = (orbit: number, axis: number) => -bound(((1 - scatter) * orbit + scatter * reach * axis) * (1 - .88 * gather));
    const cx = spread(Math.cos(angle) * a + Math.cos(angle + 1.57) * b, Math.cos(i * 2 * Math.PI / 5));
    const cy = spread(Math.sin(angle) * a + Math.sin(angle + 1) * b, Math.sin(i * 2 * Math.PI / 5));
    if (i !== held) return { x: cx, y: cy };
    const blend = releaseTime < 0 ? 0 : smoothstep(0, releaseDuration, now - releaseTime);
    return { x: x + (cx - x) * blend, y: y + (cy - y) * blend };
  }

  function point(clientX: number, clientY: number) {
    const rect = host.getBoundingClientRect();
    const unit = 1.3 / (Math.min(rect.width, rect.height) * scale);
    return { x: (clientX - rect.left - rect.width / 2) * unit, y: (clientY - rect.top - rect.height / 2) * unit };
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
      x = selected.x;
      y = selected.y;
      releaseTime = -1;
      mount.setUniforms({ u_grab: [x, y, held, releaseTime] });
    },
    move(clientX: number, clientY: number) {
      const p = point(clientX, clientY);
      x = bound(p.x + grabOffsetX);
      y = bound(p.y + grabOffsetY);
      mount.setUniforms({ u_grab: [x, y, held, -1] });
    },
    release() {
      releaseTime = time();
      mount.setUniforms({ u_grab: [x, y, held, releaseTime] });
    },
    scatter() {
      const now = time();
      if (now - pulseTime < pulseDuration) return;
      pulseTime = now;
      mount.setUniforms({ u_pulse: pulseTime });
    },
  };
}
