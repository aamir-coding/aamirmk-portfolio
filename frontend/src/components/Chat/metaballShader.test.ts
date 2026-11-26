import { beforeEach, expect, it, vi } from "vitest";
import { mountMetaballs } from "./metaballShader";

const { getCurrentFrame, setUniforms, receiveFragment } = vi.hoisted(() => ({
  getCurrentFrame: vi.fn<() => number>(),
  setUniforms: vi.fn(),
  receiveFragment: vi.fn<(source: string) => void>(),
}));

vi.mock(import("@paper-design/shaders"), async importOriginal => {
  const paper = await importOriginal();
  return {
    ...paper,
    ShaderMount: class {
      constructor(_host: HTMLElement, source: string) { receiveFragment(source); }
      getCurrentFrame = getCurrentFrame;
      setUniforms = setUniforms;
    } as unknown as typeof paper.ShaderMount,
  };
});

beforeEach(() => vi.clearAllMocks());

it("retargets a moving drop from its displayed position and carries its velocity into release", () => {
  const host = document.createElement("div");
  vi.spyOn(host, "getBoundingClientRect").mockReturnValue(new DOMRect(0, 0, 300, 300));
  getCurrentFrame.mockReturnValue(36500);
  const drops = mountMetaballs(host);
  drops.grab(100, 100);
  drops.move(250, 100);
  const { u_from: from, u_target: targets } = setUniforms.mock.lastCall![0];
  const i = targets.findIndex((target: number[]) => target[2] === -1);
  expect(i).toBeGreaterThanOrEqual(0);
  expect(from[i][0]).toBeLessThan(targets[i][0]);
  getCurrentFrame.mockReturnValue(36600);
  drops.release();
  const release = setUniforms.mock.lastCall![0];
  expect(release.u_from[i][0]).toBeGreaterThan(from[i][0]);
  expect(release.u_from[i][0]).toBeLessThan(targets[i][0]);
  expect(release.u_target[i][0]).toBe(release.u_from[i][0]);
  expect(release.u_target[i][2]).toBeCloseTo(36.6);
  expect(release.u_velocity[i][0]).toBeGreaterThan(0);
});

it("adds the interactive field to Paper's installed metaballs and finishes a pulse before replaying", () => {
  const drops = mountMetaballs(document.createElement("div"));
  // An upstream change to the extension point must not silently remove interaction.
  const [source] = receiveFragment.mock.calls[0]!;
  expect(source).toContain("uniform highp vec3 u_from[5], u_target[5];");
  expect(source).toContain("vec3 target = u_target[i];");
  getCurrentFrame.mockReturnValue(36500);
  drops.scatter();
  getCurrentFrame.mockReturnValue(36776);
  drops.scatter();
  drops.scatterOnSend(2);
  getCurrentFrame.mockReturnValue(40000);
  drops.scatter();
  expect(setUniforms.mock.calls).toEqual([[{ u_pulse: [36.5, 1] }], [{ u_pulse: [36.5, 3] }], [{ u_pulse: [40, 1] }]]);
});
