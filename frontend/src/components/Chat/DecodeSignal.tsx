// Each column rolls through a different piece of the same small type specimen.
const columns = ["+:/=;~|", "][:=+|/", "/;~:=+|", "=:|+/~;", "|/+;~:=", "~:;|/+="];

export function DecodeSignal({ phase = "waiting" }: { phase?: "waiting" | "reveal" | "cursor" }) {
  const tracks = phase === "cursor" ? columns.slice(0, 2) : columns;
  return <span className={`decode-signal decode-${phase}`} aria-hidden="true">
    {tracks.map(symbols => <span className="decode-column" key={symbols}>
      <span>{[...symbols, symbols[0]].join("\n")}</span>
    </span>)}
  </span>;
}
