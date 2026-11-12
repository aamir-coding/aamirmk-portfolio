import { useEffect, useState } from "react";
import { fetchSharedSummary, isSummaryToken, type SharedSummary } from "../../lib/summary";
import "../../styles/summary.css";

type ViewState =
  | { status: "loading" | "unavailable" | "error" }
  | { status: "ready"; data: SharedSummary };

function ResumeSource({ section }: { section: string }) {
  return <a className="summary-source" href="/resume.pdf" referrerPolicy="no-referrer">Résumé · {section}</a>;
}

export default function SummaryPage({ token }: { token: string }) {
  const validToken = isSummaryToken(token);
  const [view, setView] = useState<ViewState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!validToken) return;
    const controller = new AbortController();
    const deadline = window.setTimeout(() => {
      controller.abort();
      setView({ status: "error" });
    }, 90_000);
    void fetchSharedSummary(token, controller.signal).then((data) => {
      if (controller.signal.aborted) return;
      setView(data ? { status: "ready", data } : { status: "unavailable" });
    }).catch(() => {
      if (!controller.signal.aborted) setView({ status: "error" });
    }).finally(() => window.clearTimeout(deadline));
    return () => {
      window.clearTimeout(deadline);
      controller.abort();
    };
  }, [attempt, token, validToken]);

  const summary = view.status === "ready" ? view.data.summary : null;
  return (
    <main className="summary-page">
      <nav className="summary-toolbar" aria-label="Summary actions">
        <a href="/" referrerPolicy="no-referrer">Back to chat</a>
        {summary && (
          <button type="button" className="btn btn-secondary" onClick={() => window.print()}>
            Print or save as PDF
          </button>
        )}
      </nav>
      {summary ? (
        <article className="summary-sheet" aria-labelledby="summary-name">
          <header className="summary-heading">
            <h1 id="summary-name">{summary.name}</h1>
            <p>{summary.headline}</p>
          </header>
          <section aria-labelledby="summary-strengths">
            <h2 id="summary-strengths">Strengths</h2>
            <ul>
              {summary.strengths.map((strength) => (
                <li key={strength.title}>
                  <h3>{strength.title}</h3>
                  <p>{strength.description}</p>
                  <ResumeSource section={strength.source} />
                </li>
              ))}
            </ul>
          </section>
          <section aria-labelledby="summary-projects">
            <h2 id="summary-projects">Relevant projects</h2>
            <ul>
              {summary.projects.map((project) => (
                <li key={project.id}>
                  <h3>{project.title}</h3>
                  <p>{project.description}</p>
                  <ResumeSource section={project.source} />
                </li>
              ))}
            </ul>
          </section>
          <section aria-labelledby="summary-gaps">
            <h2 id="summary-gaps">What to confirm</h2>
            <p>{summary.gaps}</p>
          </section>
          <section aria-labelledby="summary-availability">
            <h2 id="summary-availability">Availability and contact</h2>
            <p>{summary.availability}</p>
            <a href={`mailto:${summary.contact_email}`}>{summary.contact_email}</a>
          </section>
          <footer>Prepared by Aamir’s AI assistant using his published résumé.</footer>
        </article>
      ) : !validToken || view.status === "unavailable" ? (
        <p role="status">This summary link is unavailable or expired.</p>
      ) : view.status === "error" ? (
        <div>
          <p role="alert">The summary could not be loaded.</p>
          <button type="button" className="btn btn-secondary" onClick={() => {
            setView({ status: "loading" });
            setAttempt(previous => previous + 1);
          }}>Try again</button>
        </div>
      ) : (
        <p role="status">Loading team summary…</p>
      )}
    </main>
  );
}
