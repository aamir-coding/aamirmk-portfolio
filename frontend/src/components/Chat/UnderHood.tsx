import type { RequestTelemetry } from "../../lib/contracts";
import type { BrowserTiming } from "../../lib/types";
import "../../styles/under-hood.css";

interface Props {
  telemetry?: RequestTelemetry;
  browserTiming?: BrowserTiming;
  delivery?: "instant" | "cancelled" | "curated";
}

const ms = (value: number | null) => value === null ? "Unavailable" : `${Math.round(value)} ms`;

export function UnderHood({ telemetry, browserTiming, delivery }: Props) {
  return <details className="under-hood">
    <summary>Under the hood</summary>
    <p>This receipt shows how this response was produced. Retrieval scores rank sources;
      they do not prove that a claim is supported.</p>
    <dl>
      <dt>Delivery</dt><dd>{delivery ?? telemetry?.origin ?? "Receipt unavailable"}</dd>
      {delivery === "instant" || delivery === "curated" ? <>
        <dt>Model calls</dt><dd>None — saved authored response</dd>
      </> : null}
      {delivery === "cancelled" ? <><dt>Usage</dt><dd>Unknown / incomplete — request stopped</dd></> : null}
      {telemetry ? <>
        <dt>Server total</dt><dd>{ms(telemetry.total_ms)}</dd>
        <dt>Server first text</dt><dd>{ms(telemetry.first_text_ms)}</dd>
        <dt>Tokens in / out</dt><dd>{telemetry.usage_complete
          ? `${telemetry.input_tokens} / ${telemetry.output_tokens}` : "Unknown / incomplete"}</dd>
        <dt>Prompt version</dt><dd>{telemetry.prompt_sha256 ?? "Unavailable"}</dd>
        <dt>Index version</dt><dd>{telemetry.index_sha256 ?? "Unavailable"}</dd>
        <dt>Index built</dt><dd>{telemetry.index_built_at ?? "Unavailable"}</dd>
      </> : null}
      {browserTiming ? <>
        <dt>Browser total</dt><dd>{ms(browserTiming.total_ms)}</dd>
        <dt>Browser first text</dt><dd>{ms(browserTiming.first_text_ms)}</dd>
      </> : null}
    </dl>
    {telemetry ? <>
      <h4>Measured server stages</h4>
      <dl>{Object.entries(telemetry.stages_ms).map(([name, duration]) =>
        <div key={name}><dt>{name.replaceAll("_", " ")}</dt><dd>{ms(duration)}</dd></div>)}</dl>
      {telemetry.calls.length ? <>
        <h4>Model calls</h4>
        <ol>{telemetry.calls.map((call, i) => <li key={i}>
          {call.stage.replaceAll("_", " ")} — {call.reported_model ?? call.configured_model ?? "Model unavailable"}
          {` · ${ms(call.duration_ms)} · ${call.status} · usage ${call.usage_source}`}
          {call.usage_source !== "unknown" ? ` · ${call.input_tokens} in / ${call.output_tokens} out` : ""}
        </li>)}</ol>
      </> : null}
      {telemetry.retrieval.length ? <>
        <h4>Retrieved public sources</h4>
        {telemetry.retrieval.map((retrieval, i) => <div key={i}>
          <p>{retrieval.stage} ({ms(retrieval.duration_ms)})</p>
          <ol>{retrieval.chunks.map((chunk) => <li key={chunk.id}>
            {chunk.id}: {chunk.score.toFixed(5)} ({chunk.method})
          </li>)}</ol>
        </div>)}
      </> : null}
    </> : null}
    <p>Server measurements exclude network transit. Browser measurements include it.
      Missing provider counts are never estimated in this receipt.</p>
  </details>;
}
