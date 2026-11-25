import type { ProjectCardData } from "../../lib/types";
import { projects, type ShowcaseId } from "./projects";

export function SelectedWork({ projectId, card, onSelect, onAsk, onSample, disabled }: {
  projectId?: ShowcaseId;
  card?: ProjectCardData;
  onSelect: (id: ShowcaseId) => void;
  onAsk: (question: string) => void;
  onSample: () => void;
  disabled: boolean;
}) {
  const project = projects.find(item => item.id === projectId);
  if (project) return <article className="project-detail">
    <picture><source media="(max-width: 600px)" srcSet={project.mobile} />
      <img src={project.image} alt={project.alt} />
    </picture>
    <p>{project.description}</p>
    {card && <details className="project-architecture">
      <summary>Inspect architecture</summary>
      <p>{card.subtitle} · {card.role}</p>
      <p>{card.summary}</p>
      <p className="architecture-description">{card.architecture_details}</p>
      <ul>{card.highlights.map(item => <li key={item}>{item}</li>)}</ul>
      <p>{card.tech_stack.join(", ")}</p>
      {card.metrics && <dl>{Object.entries(card.metrics).map(([key, value]) =>
        <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl>}
      {card.source_sections.length > 0 && <p>Source sections: {card.source_sections.join(", ")}</p>}
    </details>}
    <div className="project-links">
      <a href={project.demo} target="_blank" rel="noreferrer">{project.demoLabel}</a>
      <a href={project.source} target="_blank" rel="noreferrer">View {project.title} source</a>
    </div>
    <button className="project-ask" type="button" disabled={disabled} onClick={() => onAsk(project.question)}>Ask about this project</button>
    {project.id === "ai-digital-assistant" && <button className="text-action" disabled={disabled} onClick={onSample}>Try the sample answer</button>}
  </article>;
  return <>
    {projects.map(item => <button className="project-row" key={item.id} onClick={() => onSelect(item.id)}>
      <img src={item.mobile} alt="" /><span>{item.title}</span><span aria-hidden="true">→</span>
    </button>)}
    <CandidateDetails />
  </>;
}

export function CandidateDetails() {
  return <section className="portfolio-details">
    <h3>Profile</h3>
    <p>MSRUAS B.Tech (CGPA 9.77/10), Bengaluru, India. Available for hire.</p>
    <dl><dt>Core focus</dt><dd>LLM pipelines, hybrid retrieval, and asynchronous services</dd>
      <dt>Primary stack</dt><dd>Python, FastAPI, Groq, React, TypeScript, Docker</dd></dl>
  </section>;
}
