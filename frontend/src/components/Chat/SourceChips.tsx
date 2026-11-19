import React from "react";
import { formatPublicSourceHref } from "./formatHelpers";
import type { SourceCitation } from "../../lib/types";

export interface SourceChipsProps {
  sources: SourceCitation[];
}

export const SourceChips = React.memo(function SourceChips({
  sources,
}: SourceChipsProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div
      className="source-chips-container"
      role="group"
      aria-label="Answer sources"
    >
      <details>
        <summary className="source-chips-label">Sources <span>{sources.length}</span></summary>
        <ul className="source-chips-list" role="list">
          {sources.map((src) => {
            const sectionBadge = src.source_section ? `[${src.source_section}]` : "";
            const safeUrl = formatPublicSourceHref(src.source_url ?? undefined);

            return (
              <li key={src.chunk_id} className="source-chip-item">
                {safeUrl ? (
                  <a
                    href={safeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="source-chip source-chip-link"
                    aria-label={`${src.title} ${sectionBadge} (opens external link)`}
                  >
                    <span className="source-chip-title">{src.title}</span>
                    {sectionBadge && (
                      <span className="source-chip-section">{sectionBadge}</span>
                    )}
                  </a>
                ) : (
                  <span className="source-chip">
                    <span className="source-chip-title">{src.title}</span>
                    {sectionBadge && (
                      <span className="source-chip-section">{sectionBadge}</span>
                    )}
                    <span className="source-chip-section">Reference only</span>
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      </details>
    </div>
  );
});
