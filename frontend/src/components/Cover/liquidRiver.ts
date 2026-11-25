import { liquidMetalFragmentShader, ShaderMount } from "@paper-design/shaders";
import texture from "./art/river-texture.png";

export async function mountRiver(host: HTMLElement, current: () => boolean) {
  return mountLiquidMetal(host, texture, current);
}

export async function mountLiquidMetal(host: HTMLElement, mask: string, current: () => boolean) {
  const image = new Image();
  image.src = mask;
  await image.decode();
  if (!current()) return;
  // Each silhouette carries the edge field baked by Paper's image processor.
  const mount = new ShaderMount(host, liquidMetalFragmentShader, {
    u_image: image, u_isImage: true, u_shape: 0, u_colorBack: [0, 0, 0, 0],
    u_colorTint: [1, 1, 1, 0], u_repetition: 2.5, u_shiftRed: 0, u_shiftBlue: 0,
    u_contour: .66, u_softness: .13, u_distortion: .12, u_angle: 64,
    u_originX: .5, u_originY: .5, u_worldWidth: 0, u_worldHeight: 0,
    u_fit: 1, u_scale: 1, u_rotation: 0, u_offsetX: 0, u_offsetY: 0,
  }, { alpha: true }, 0, 11400, 1, 95000, ["u_image"]);
  return mount;
}
