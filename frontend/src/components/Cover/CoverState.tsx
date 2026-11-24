import type { Ref } from "react";
import type { CompanyContext } from "../../lib/api";

export function CoverState({ headingRef, company }: {
  headingRef: Ref<HTMLHeadingElement>;
  company: CompanyContext | null;
}) {
  return <div className="portfolio-identity">
    <p className="portfolio-role">AI Systems &amp; Full-Stack Engineer</p>
    <h1 id="main-heading" ref={headingRef} tabIndex={-1}>Ask about<br /><em>Aamir.</em></h1>
    <p className="portfolio-pitch">Explore his projects, experience, and the engineering decisions behind his work.</p>
    {company && <p className="portfolio-greeting">{company.greeting}</p>}
  </div>;
}
