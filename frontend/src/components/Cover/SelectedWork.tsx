const projects = [
  {
    id: "entropy",
    title: "Entropy Online Judge",
    summary: "Built a coding workspace and asynchronous C++ and Python judging with per-submission isolation and resource limits.",
    href: "https://entropy-oj.vercel.app/",
    link: "Open Entropy Online Judge",
  },
  {
    id: "portfolio-assistant",
    title: "AI Digital Assistant",
    summary: "Built this recruiter assistant to retrieve curated facts and stream answers with citations and project cards.",
    href: "/evals",
    link: "Read the assistant’s evaluation record",
  },
  {
    id: "health-tracker",
    title: "HealthTracker",
    summary: "Built a web app for nutrition, workouts, and health metrics with interactive dashboards and cache-first data access.",
    href: "https://github.com/aamir-coding/health-tracker",
    link: "View HealthTracker source",
  },
] as const;

export function SelectedWork() {
  return (
    <section className="portfolio-measure portfolio-work">
      <h2 id="work" tabIndex={-1}>Selected work</h2>
      <ul>
        {projects.map(project => (
          <li key={project.id}>
            <article id={project.id}>
              <h3>{project.title}</h3>
              <p>{project.summary}</p>
              <a href={project.href}>{project.link}</a>
            </article>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function CandidateDetails() {
  return (
    <section className="portfolio-details">
      <h2>Profile</h2>
      <p>MSRUAS B.Tech (CGPA 9.77/10), Bengaluru, India. Available for hire.</p>
      <dl>
        <dt>Core focus</dt>
        <dd>LLM pipelines, hybrid retrieval, and asynchronous services</dd>
        <dt>Primary stack</dt>
        <dd>Python, FastAPI, Groq, React, TypeScript, Docker</dd>
      </dl>
      <nav aria-label="Direct candidate links">
        <a href="https://github.com/aamir-coding" target="_blank" rel="noopener noreferrer">GitHub</a>
        <a href="https://www.linkedin.com/in/aamir-mk/" target="_blank" rel="noopener noreferrer">LinkedIn</a>
        <a href="mailto:aamirmkh25@gmail.com">Email Aamir</a>
      </nav>
    </section>
  );
}
