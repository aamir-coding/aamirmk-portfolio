/** Source receipts are shown separately. Leave ordinary prose, links and code intact. */
export function answerProse(raw: string, streaming = false): string {
  const marker = /\x60+|~{3,}|[*_]{0,2}【|[*_]{0,2}[([][ \t]*[*_]{0,2}sources?[*_]{0,2}[ \t]*:|^[ \t]*[*_]{0,2}sources?[*_]{0,2}[ \t]*:/gim;
  let output = "";
  let cursor = 0;
  for (let match = marker.exec(raw); match; match = marker.exec(raw)) {
    const start = match.index;
    const token = match[0];
    output += raw.slice(cursor, start);
    if (token[0] === "\x60" || token.startsWith("~")) {
      const close = raw.indexOf(token, marker.lastIndex);
      if (close === -1) return output + raw.slice(start);
      cursor = close + token.length;
      output += raw.slice(start, cursor);
      marker.lastIndex = cursor;
      continue;
    }

    // A receipt may span provider tokens and contain nested parentheses in its title.
    const open = token.match(/[【([]/)?.[0];
    const endOfLine = raw.indexOf("\n", marker.lastIndex);
    const limit = endOfLine === -1 ? raw.length : endOfLine;
    cursor = marker.lastIndex;
    if (open) {
      const close = open === "【" ? "】" : open === "(" ? ")" : "]";
      let depth = 1;
      while (cursor < limit && depth) {
        const c = raw[cursor++];
        if (c === open) depth++;
        if (c === close) depth--;
      }
      if (open === "[" && !depth && raw[cursor] === "(") {
        output += raw.slice(start, cursor);
        marker.lastIndex = cursor;
        continue;
      }
      const emphasis = token.match(/^[*_]+/)?.[0];
      if (emphasis) {
        if (raw.startsWith(emphasis, cursor)) cursor += emphasis.length;
        else if (!depth) output += emphasis;
      }
    } else {
      // Keep a user-requested link even if the model puts a Source: label on its line.
      const line = raw.slice(cursor, limit);
      if (/https?:\/\//i.test(line)) output += line.replace(/^[*_]{0,2}[ \t]*/, "");
      cursor = limit;
    }
    output = output.replace(/[ \t]+$/, "");
    cursor += raw.slice(cursor).match(/^[ \t]+(?=[.,;:!?])/)?.[0].length ?? 0;
    if (output.endsWith(".") && raw[cursor] === ".") cursor++;
    marker.lastIndex = cursor;
  }

  let tail = raw.slice(cursor);
  if (streaming) {
    // Wait for enough characters to distinguish "(Sou..." from normal prose.
    tail = tail.replace(/(^|\n|[*_]{0,2}[([])[ \t]*[*_]{0,2}([a-z]*)[*_]{0,2}[ \t]*$/i,
      (part, _open: string, prefix: string) => "sources".startsWith(prefix.toLowerCase()) ? "" : part);
  }
  return output + tail;
}
