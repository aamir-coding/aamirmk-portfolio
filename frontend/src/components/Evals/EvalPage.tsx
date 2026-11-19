import { useEvalSummary } from "../../lib/evals";
import "../../styles/evals.css";

export default function EvalPage() {
  const { summary, error } = useEvalSummary();
  const report = summary?.report;

  return (
    <main className="eval-page">
      <header className="eval-heading">
        <a href="/">Return to portfolio</a>
        <h1>Evaluation record</h1>
      </header>
      {summary ? (
        <section className="eval-overview" aria-labelledby="eval-result">
          <h2 id="eval-result">{summary.badge}</h2>
          {summary.reason && <p>{summary.reason}</p>}
          {report && <>
            <p><strong>Model accuracy: unavailable.</strong> All {report.draft_chunks} public fact chunks
              remain drafts. Citation membership does not prove semantic support. Curated fit examples
              are not calibrated ground truth.</p>
            <p className="eval-run">
              Offline engineering checks replay saved fake and curated responses to check for regressions.
              {" "}Run on <time dateTime={report.generated_at}>
                {new Date(report.generated_at).toLocaleString("en", {
                  dateStyle: "medium", timeStyle: "short", timeZone: "UTC",
                })}
              </time> UTC.
            </p>
          </>}
        </section>
      ) : <p role="status">{error ? "Evaluation results unavailable. Try again later." : "Loading recorded results…"}</p>}

      {report && <div className="eval-records">
        <section aria-labelledby="eval-replay">
          <h2 id="eval-replay">Recorded response checks</h2>
          <p>{report.development_without_recordings} development cases have no saved response. They are outside the replay coverage.</p>
          <table>
            <caption>Saved responses by category</caption>
            <thead><tr><th scope="col">Category</th><th scope="col">Passed / total</th><th scope="col">Skipped</th></tr></thead>
            <tbody>{report.categories.map((row) => (
              <tr key={row.category}>
                <th scope="row">{row.category}</th><td>{row.passed} / {row.total}</td><td>{row.skipped}</td>
              </tr>
            ))}</tbody>
          </table>
        </section>

        <section aria-labelledby="eval-retrieval">
          <h2 id="eval-retrieval">Local retrieval</h2>
          <p>Hit measures whether a relevant source appears. Recall measures coverage of exhaustively
            labeled sources. MRR measures the first relevant source’s rank. Alternative-source labels
            have no recall denominator. These scores measure retrieval only.</p>
          <table className="eval-retrieval-table">
            <caption>Development retrieval metrics</caption>
            <thead><tr><th scope="col">Suite</th><th scope="col">Metric</th><th scope="col">Value</th><th scope="col">Queries</th></tr></thead>
            <tbody>{report.retrieval.map((row) => (
              <tr key={`${row.suite}-${row.metric}`}>
                <th scope="row">{row.suite.replaceAll("_", " ")}</th>
                <td>{row.metric.replaceAll("_", " ")}</td>
                <td>{row.denominator ? (row.numerator / row.denominator).toFixed(4) : "Unavailable"}</td>
                <td>{row.denominator}</td>
              </tr>
            ))}</tbody>
          </table>
        </section>

        <section aria-labelledby="eval-agreement">
          <h2 id="eval-agreement">Human and judge agreement</h2>
          <p>Historical independent validation gate <strong>{report.judge_validation.status}</strong>.
            {" "}The utility model ({report.judge_validation.model}) graded eight authored validation
            answers against Aamir’s frozen grades after twenty calibration examples. The models share a family.
            This small sample measured agreement on the corpus before the résumé refresh.</p>
          <table className="eval-agreement-table">
            <caption>Independent validation agreement (80% floor per axis)</caption>
            <thead><tr><th scope="col">Axis</th><th scope="col">Agreement</th><th scope="col">Disagreements</th></tr></thead>
            <tbody>{Object.entries(report.judge_validation.axes).map(([axis, count]) => (
              <tr key={axis}>
                <th scope="row">{axis}</th>
                <td>{count.passed} / {count.total} ({(count.passed / count.total * 100).toFixed(1)}%)</td>
                <td>{report.judge_validation.failures_by_axis[axis]}</td>
              </tr>
            ))}</tbody>
          </table>
          <ul>{report.judge_validation.disagreements.map((row) => (
            <li key={`${row.item_id}-${row.axis}`}>{row.item_id}, {row.axis} (human {row.human}, judge {row.judge})</li>
          ))}</ul>
          <p>All disagreements and original human grades are retained. No failed judgment was retried
            to improve a score. {report.judge_validation.status === "failed" && "The failed gate remains the accepted empirical baseline."}</p>
        </section>

        <section aria-labelledby="eval-coverage">
          <h2 id="eval-coverage">Failures and reserved evidence</h2>
          {report.failed_checks.length ? (
            <ul>{report.failed_checks.map((failure) => <li key={failure}>{failure}</li>)}</ul>
          ) : <p>No offline retrieval or replay gate failures in this artifact.</p>}
          <p>{report.held_out_reserved} held-out cases remain reserved and unexecuted. This page withholds their text, IDs,
            and expected answers. The author has seen the cases. Further judge tuning needs a fresh independent validation set.</p>
        </section>

        <details className="eval-provenance">
          <summary>Artifact provenance</summary>
          <dl>
            <dt>Source commit</dt><dd>{report.source_commit}{report.source_dirty ? " (working tree had changes)" : " (clean)"}</dd>
            <dt>Result SHA-256</dt><dd>{report.source_result_sha256}</dd>
            <dt>Judge validation SHA-256</dt><dd>{report.judge_validation.artifact_sha256}</dd>
            <dt>Rubric SHA-256</dt><dd>{report.judge_validation.rubric_sha256}</dd>
          </dl>
        </details>
      </div>}
    </main>
  );
}
