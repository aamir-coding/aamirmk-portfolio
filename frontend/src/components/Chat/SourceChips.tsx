import React from "react";
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
      aria-label="Verified Source Receipts"
    >
      <span className="source-chips-label">RECEIPTS:</span>
      <ul className="source-chips-list">
        {sources.map((src) => {
          const sectionBadge = src.source_section ? `[${src.source_section}]` : "";
          const hasUrl = Boolean(src.source_url);

          return (
            <li key={src.chunk_id} className="source-chip-item">
              {hasUrl ? (
                <a
                  href={src.source_url!}
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
                  title={`Grounded in questionnaire receipt: ${src.title}`}
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
