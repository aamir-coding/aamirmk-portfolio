import savedAnswer from "./art/assistant-saved-answer.webp";

const projects = [
  {
    id: "entropy",
    title: "Entropy Online Judge",
    summary: "During his AlgoUniversity externship, Aamir built a coding workspace and asynchronous C++ and Python judging. Each submission runs in its own workspace with time, output, and resource limits.",
    demo: "https://entropy-oj.vercel.app/",
    source: "https://github.com/aamir-coding/entropy-oj",
    demoLabel: "Open Entropy Online Judge",
    sourceLabel: "View Entropy source",
  },
  {
    id: "health-tracker",
    title: "HealthTracker",
    summary: "Aamir built a progressive web app for tracking nutrition, workouts, and health metrics, with interactive dashboards and cache-first data access.",
    demo: "https://health-tracker-alpha-one.vercel.app/",
    source: "https://github.com/aamir-coding/health-tracker",
    demoLabel: "Open HealthTracker",
    sourceLabel: "View HealthTracker source",
  },
] as const;

export function SelectedWork() {
  return (
    <section className="portfolio-measure portfolio-work" aria-labelledby="work">
      <h2 id="work" tabIndex={-1}>Selected work</h2>
      <article id="portfolio-assistant" className="portfolio-work-feature" aria-labelledby="portfolio-assistant-title">
        <div className="portfolio-work-feature-copy">
          <h3 id="portfolio-assistant-title">AI Digital Assistant</h3>
          <p>
            Aamir built this recruiter assistant to search curated facts with BM25 and embeddings,
            stream answers with citations, and display project cards through validated tool calls.
          </p>
          <div className="portfolio-work-links">
            <a href="/evals">Read the assistant’s evaluation record</a>
            <a href="https://github.com/aamir-coding/aamirmk-portfolio">View assistant source</a>
          </div>
        </div>
        <figure className="portfolio-work-figure">
          <div className="portfolio-work-example">
            <div className="portfolio-work-example-copy">
              <p><strong>“What did Aamir build at AlgoUniversity?”</strong></p>
              <p>
                Aamir built Entropy’s coding workspace with compiler diagnostics and submission history,
                plus an asynchronous C++ and Python judging queue.
              </p>
            </div>
            <img
              src={savedAnswer}
              width={698}
              height={480}
              alt=""
              loading="lazy"
              decoding="async"
              onError={event => { event.currentTarget.hidden = true; }}
            />
          </div>
          <figcaption>From the saved answer, with the résumé and Entropy demo as sources.</figcaption>
        </figure>
      </article>
      <ul className="portfolio-work-list" role="list">
        {projects.map(project => (
          <li key={project.id}>
            <article id={project.id} aria-labelledby={`${project.id}-title`}>
              <h3 id={`${project.id}-title`}>{project.title}</h3>
              <p>{project.summary}</p>
              <div className="portfolio-work-links">
                <a href={project.demo}>{project.demoLabel}</a>
                <a href={project.source}>{project.sourceLabel}</a>
              </div>
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
    </section>
  );
}
