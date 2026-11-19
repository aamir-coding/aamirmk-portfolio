import { useState } from "react";
import savedAnswer from "./art/assistant-saved-answer.webp";
import savedAnswerMobile from "./art/assistant-answer-mobile.webp";
import entropyWorkspace from "./art/entropy-workspace.webp";
import entropyMobile from "./art/entropy-workspace-mobile.webp";
import healthTracker from "./art/healthtracker-demo.webp";

interface Screenshot {
  src: string;
  width: number;
  height: number;
  alt: string;
  mobile?: { src: string; width: number; height: number };
  caption?: string;
  fallback?: string;
}

const projects = [
  {
    id: "entropy",
    title: "Entropy Online Judge",
    summary: "During his AlgoUniversity externship, Aamir built a coding workspace and asynchronous C++ and Python judging. Each submission runs in its own workspace with time, output, and resource limits.",
    demo: "https://entropy-oj.vercel.app/",
    source: "https://github.com/aamir-coding/entropy-oj",
    demoLabel: "Open Entropy Online Judge",
    sourceLabel: "View Entropy source",
    screenshot: {
      src: entropyWorkspace,
      width: 1000,
      height: 600,
      alt: "The Entropy Two Sum workspace in the C++ code editor",
      mobile: { src: entropyMobile, width: 465, height: 295 },
    },
  },
  {
    id: "health-tracker",
    title: "HealthTracker",
    summary: "Aamir built a progressive web app for tracking nutrition, workouts, and health metrics, with interactive dashboards and cache-first data access.",
    demo: "https://health-tracker-alpha-one.vercel.app/",
    source: "https://github.com/aamir-coding/health-tracker",
    demoLabel: "Open HealthTracker",
    sourceLabel: "View HealthTracker source",
    screenshot: {
      src: healthTracker,
      width: 850,
      height: 637,
      alt: "HealthTracker’s demo dashboard with activity and goal tracking",
      caption: "HealthTracker’s public demo account.",
    },
  },
] as const;

function ProjectScreenshot({ src, width, height, alt, mobile, caption, fallback }: Screenshot) {
  const [failed, setFailed] = useState(false);
  return (
    <figure className="portfolio-work-figure">
      <picture>
        {mobile && <source media="(max-width: 700px)" srcSet={mobile.src} width={mobile.width} height={mobile.height} />}
        <img
          src={src}
          width={width}
          height={height}
          alt={alt}
          loading="lazy"
          decoding="async"
          hidden={failed}
          onError={() => setFailed(true)}
          onLoad={() => setFailed(false)}
        />
      </picture>
      {failed && fallback && <p>{fallback}</p>}
      {caption && <figcaption>{caption}</figcaption>}
    </figure>
  );
}

interface SelectedWorkProps {
  onTrySample: () => void;
  sampleDisabled: boolean;
}

export function SelectedWork({ onTrySample, sampleDisabled }: SelectedWorkProps) {
  return (
    <section className="portfolio-measure portfolio-work" aria-labelledby="work">
      <div className="portfolio-work-heading">
        <h2 id="work" tabIndex={-1}>Selected work</h2>
        <a href="https://github.com/aamir-coding">GitHub profile</a>
      </div>
      <article id="portfolio-assistant" className="portfolio-work-feature" aria-labelledby="portfolio-assistant-title">
        <div className="portfolio-work-feature-copy">
          <h3 id="portfolio-assistant-title">AI Digital Assistant</h3>
          <p>
            Aamir built this recruiter assistant to search curated facts with BM25 and embeddings,
            stream answers with citations, and display project cards through validated tool calls.
          </p>
          <div className="portfolio-work-links">
            <button type="button" onClick={onTrySample} disabled={sampleDisabled}>Try the sample answer</button>
            <a href="/evals">Read the assistant’s evaluation record</a>
            <a href="https://github.com/aamir-coding/aamirmk-portfolio">View assistant source</a>
          </div>
        </div>
        <ProjectScreenshot
          src={savedAnswer}
          width={747}
          height={490}
          mobile={{ src: savedAnswerMobile, width: 327, height: 402 }}
          alt="Assistant answer about Entropy’s coding workspace, compiler diagnostics, submission history, and asynchronous C++ and Python judging"
          caption="A replayed answer about Aamir’s work at AlgoUniversity."
          fallback="Aamir built Entropy’s coding workspace with compiler diagnostics and submission history, plus an asynchronous queue for judging C++ and Python submissions."
        />
      </article>
      <ul className="portfolio-work-list" role="list">
        {projects.map(project => (
          <li key={project.id}>
            <article id={project.id} aria-labelledby={`${project.id}-title`}>
              <ProjectScreenshot {...project.screenshot} />
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
