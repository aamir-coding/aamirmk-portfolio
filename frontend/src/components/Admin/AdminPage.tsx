import { useEffect, useId, useRef, useState, type FormEvent, type ReactNode } from "react";
import { AdminRequestError, fetchDashboard, type Dashboard } from "../../lib/admin";
import "../../styles/admin.css";

const numbers = new Intl.NumberFormat("en");
const dateTime = new Intl.DateTimeFormat("en", {
  dateStyle: "medium", timeStyle: "short", timeZone: "UTC",
});
const formatCount = (count: number) => numbers.format(count);
const formatTime = (time: string) => dateTime.format(new Date(time));

interface RecordsProps {
  title: string;
  columns: string[];
  rows: { key: string; cells: ReactNode[] }[];
  empty: string;
}

function Records({ title, columns, rows, empty }: RecordsProps) {
  const heading = useId();
  return (
    <section className="admin-records" aria-labelledby={heading}>
      <h2 id={heading}>{title}</h2>
      {rows.length === 0 ? <p>{empty}</p> : (
        <div className="admin-table-scroll" role="region" aria-labelledby={heading} tabIndex={0}>
          <table>
            <thead><tr>{columns.map(column => <th key={column} scope="col">{column}</th>)}</tr></thead>
            <tbody>{rows.map(row => (
              <tr key={row.key}>
                {row.cells.map((cell, index) => <td key={columns[index]}>{cell}</td>)}
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function RecruiterActivity({ data }: { data: Dashboard }) {
  const unansweredRate = data.classified_questions > 0
    ? `${Math.round(100 * data.unanswered_count / data.classified_questions)}%`
    : "—";
  return (
    <>
      <p className="admin-date-range">
        <time dateTime={data.start_date}>{data.start_date}</time> to{" "}
        <time dateTime={data.end_date}>{data.end_date}</time> UTC
      </p>
      <dl className="admin-metrics">
        <div><dt>Recorded questions</dt><dd>{formatCount(data.question_count)}</dd></div>
        <div>
          <dt>Handoff offer rate</dt>
          <dd>
            {unansweredRate}
            <small>{data.unanswered_count} of {data.classified_questions} classified questions</small>
          </dd>
        </div>
        <div><dt>Mean chat latency</dt><dd>{data.average_latency_ms === null ? "—" : `${Math.round(data.average_latency_ms)} ms`}</dd></div>
        <div><dt>Completed fit reports</dt><dd>{formatCount(data.fit_reports)}</dd></div>
        <div><dt>Handoff requests</dt><dd>{formatCount(data.handoff_count)}</dd></div>
        <div><dt>Candidate eval cases</dt><dd>{formatCount(data.candidate_count)}</dd></div>
      </dl>
      <div className="admin-grid">
        <Records
          title="Daily token usage" columns={["UTC day", "Known tokens", "Runs with unknown usage", "Configured ceiling"]}
          rows={data.usage.map(day => ({
            key: day.day, cells: [day.day, formatCount(day.known_tokens), formatCount(day.unknown_runs), formatCount(data.daily_token_ceiling)],
          }))}
          empty="No usage recorded."
        />
        <Records
          title="Company opens" columns={["Company link", "Opens"]}
          rows={data.company_opens.map(row => ({ key: row.slug, cells: [row.slug, formatCount(row.count)] }))}
          empty="No company opens recorded."
        />
        <Records
          title="Top questions" columns={["Question", "Count"]}
          rows={data.top_questions.map(row => ({ key: row.question, cells: [row.question, formatCount(row.count)] }))}
          empty="No questions recorded."
        />
        <Records
          title="Unanswered questions" columns={["Question offered a handoff", "Time (UTC)"]}
          rows={data.unanswered.map(row => ({ key: row.id, cells: [row.question, formatTime(row.created_at)] }))}
          empty="No handoff offers recorded."
        />
        <Records
          title="Handoffs" columns={["Latest visitor question", "Reply email", "Delivery", "Time (UTC)"]}
          rows={data.handoffs.map(row => ({
            key: row.id, cells: [row.question ?? "—", row.reply_email ?? "—", row.delivery_status, formatTime(row.created_at)],
          }))}
          empty="No handoffs submitted."
        />
        <Records
          title="Feedback" columns={["Question", "Rating", "Reason", "Time (UTC)"]}
          rows={data.feedback.map(row => ({
            key: row.id, cells: [row.question, row.rating === "up" ? "Helpful" : "Not helpful", row.reason ?? "—", formatTime(row.created_at)],
          }))}
          empty="No feedback submitted."
        />
        <Records
          title="Candidate eval cases" columns={["Question", "Downvote reason", "Time (UTC)"]}
          rows={data.candidates.map(row => ({
            key: row.id, cells: [row.question, row.reason ?? "—", formatTime(row.created_at)],
          }))}
          empty="No downvotes to review."
        />
      </div>
    </>
  );
}

export default function AdminPage() {
  const request = useRef<AbortController | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<Dashboard | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => () => {
    request.current?.abort();
    request.current = null;
  }, []);

  async function load(bearer: string) {
    if (!bearer || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    const timeout = window.setTimeout(() => controller.abort(), 15_000);
    setBusy(true);
    setError(null);
    try {
      const snapshot = await fetchDashboard(bearer, controller.signal);
      if (request.current === controller) {
        setToken(bearer);
        setData(snapshot);
      }
    } catch (cause) {
      if (request.current === controller) {
        if (cause instanceof AdminRequestError && [401, 404].includes(cause.status)) {
          setToken(null);
          setData(null);
        }
        setError(controller.signal.aborted || !(cause instanceof Error)
          ? "The dashboard could not be loaded."
          : cause.message);
      }
    } finally {
      window.clearTimeout(timeout);
      if (request.current === controller) {
        request.current = null;
        setBusy(false);
      }
    }
  }

  function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const bearer = String(new FormData(form).get("token") ?? "").trim();
    form.reset();
    void load(bearer);
  }

  function signOut() {
    request.current?.abort();
    request.current = null;
    setToken(null);
    setData(null);
    setError(null);
    setBusy(false);
  }

  return (
    <main className="admin-page">
      <header className="admin-header">
        <div><a href="/">Portfolio</a><h1>Recruiter analytics</h1></div>
        {token && (
          <div className="admin-actions">
            <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void load(token)}>Refresh</button>
            <button type="button" className="btn btn-secondary" onClick={signOut}>Sign out</button>
          </div>
        )}
      </header>
      {!token && (
        <form className="admin-login" onSubmit={signIn}>
          <label>Admin token <input type="password" name="token" maxLength={128} autoComplete="off" required /></label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? "Opening…" : "Open dashboard"}
          </button>
        </form>
      )}
      {error && <p role="alert">{error}</p>}
      {data && <RecruiterActivity data={data} />}
    </main>
  );
}
