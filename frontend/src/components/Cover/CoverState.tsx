import type { Ref } from "react";
import type { CompanyContext } from "../../lib/api";

interface CoverStateProps {
  headingRef: Ref<HTMLHeadingElement>;
  company: CompanyContext | null;
}

export function CoverState({ headingRef, company }: CoverStateProps) {
  return (
    <div className="portfolio-identity">
      <h1 id="main-heading" ref={headingRef} tabIndex={-1}>
        <span>Aamir</span>{" "}<span>Mohammed Khan</span>
      </h1>
      <p className="portfolio-role">AI Systems &amp; Full-Stack Engineer</p>
      {company && <p className="portfolio-greeting">{company.greeting}</p>}
    </div>
  );
}
