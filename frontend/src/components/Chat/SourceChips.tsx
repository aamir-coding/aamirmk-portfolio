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
      aria-label="Verified Source Receipts"
    >
      <span className="source-chips-label">RECEIPTS:</span>
      <ul className="source-chips-list">
        {sources.map((src) => {
          const sectionBadge = src.source_section ? `[${src.source_section}]` : "";
          const safeUrl = formatPublicSourceHref(src.source_url ?? undefined);
          const hasUrl = Boolean(safeUrl);

          return (
            <li key={src.chunk_id} className="source-chip-item">
              {hasUrl ? (
                <a
                  href={safeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-chip source-chip-link"
                  title={`View verified receipt: ${src.title}`}
                  aria-label={`${src.title} ${sectionBadge} (opens external link)`}
                >
                  {sectionBadge && (
                    <span className="source-chip-section">{sectionBadge}</span>
                  )}
                  <span className="source-chip-title">{src.title}</span>
                  <span className="source-chip-icon" aria-hidden="true">
                    ↗
                  </span>
                </a>
              ) : (
                <span
                  className="source-chip"
                  role="group"
                  title={src.source_url ? `Source not publicly accessible. Receipt: ${src.title}` : `Grounded in questionnaire receipt: ${src.title}`}
                  aria-label={`${src.title} ${sectionBadge}`}
                >
                  {sectionBadge && (
                    <span className="source-chip-section">{sectionBadge}</span>
                  )}
                  <span className="source-chip-title">{src.title}</span>
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
});
