import { expect, it, vi } from "vitest";
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

it("adds the interactive field to Paper's installed metaballs and finishes a pulse before replaying", () => {
  const drops = mountMetaballs(document.createElement("div"));
  // An upstream change to the extension point must not silently remove interaction.
  const [source] = receiveFragment.mock.calls[0]!;
  expect(source).toContain("uniform vec4 u_grab;");
  expect(source).toContain("traj = mix(traj, -u_grab.xy, held);");
  getCurrentFrame.mockReturnValue(36500);
  drops.scatter();
  getCurrentFrame.mockReturnValue(36776);
  drops.scatter();
  getCurrentFrame.mockReturnValue(37700);
  drops.scatter();
  expect(setUniforms.mock.calls).toEqual([[{ u_pulse: 36.5 }], [{ u_pulse: 37.7 }]]);
});
