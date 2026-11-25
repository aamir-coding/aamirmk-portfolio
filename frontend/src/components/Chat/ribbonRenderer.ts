import vertexSource from "./ribbon.vertex.glsl?raw";
import fragmentSource from "./ribbon.fragment.glsl?raw";

export function mountRibbon(canvas: HTMLCanvasElement) {
  const gl = canvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false });
  if (!gl) return;
  const program = gl.createProgram();
  if (!program) return;
  for (const [type, source] of [[gl.VERTEX_SHADER, vertexSource], [gl.FRAGMENT_SHADER, fragmentSource]] as const) {
    const shader = gl.createShader(type);
    if (shader) {
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      gl.attachShader(program, shader);
      gl.deleteShader(shader);
    }
  }
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    gl.deleteProgram(program);
    return;
  }
  gl.useProgram(program);
  const vertices: number[] = [];
  for (let i = 0; i < 128; i++) {
    const y = i / 64 - 1, next = y + 1 / 64;
    vertices.push(-1,y, 1,y, -1,next, 1,y, 1,next, -1,next);
  }
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STATIC_DRAW);
  const position = gl.getAttribLocation(program, "param");
  gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
  gl.enableVertexAttribArray(position);
  gl.enable(gl.DEPTH_TEST);
  const phase = gl.getUniformLocation(program, "phase");
  const night = gl.getUniformLocation(program, "dark");
  let frame = 0;
  let angle = 0;
  let graphite = false;
  const resize = () => {
    const width = Math.max(1, Math.min(320, Math.ceil(canvas.clientWidth * devicePixelRatio)));
    if (canvas.width !== width || canvas.height !== Math.round(width * 1.25)) {
      canvas.width = width;
      canvas.height = Math.round(width * 1.25);
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
  };
  const draw = () => {
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.uniform1f(phase, angle);
    gl.uniform1f(night, Number(graphite));
    gl.drawArrays(gl.TRIANGLES, 0, vertices.length / 2);
  };
  function stop() { cancelAnimationFrame(frame); }
  return {
    theme(dark: boolean) { graphite = dark; resize(); draw(); },
    stop,
    sweep(distance: number, duration: number) {
      stop();
      const start = performance.now(), from = angle;
      function tick(now: number) {
        const progress = Math.min(1, (now - start) / duration);
        angle = from + distance * (1 - (1 - progress) ** 2);
        draw();
        if (progress < 1) frame = requestAnimationFrame(tick);
      }
      frame = requestAnimationFrame(tick);
    },
    dispose() {
      stop();
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
      gl.getExtension("WEBGL_lose_context")?.loseContext();
    },
  };
}
