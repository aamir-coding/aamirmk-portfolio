import { useEvalSummary } from "../../lib/evals";
import "../../styles/evals.css";

export default function EvalPage() {
  const { summary, error } = useEvalSummary();
  const report = summary?.report;
  return <main className="eval-page">
    <a href="/">Return to portfolio</a>
    <h1>Evaluation record</h1>
    <p>Tests, measured outcomes, and the limits of the evidence.</p>
    {!summary ? <p role="status">{error ? "Evaluation results unavailable. Try again later." : "Loading recorded results…"}</p> : <>
      <h2>{summary.badge}</h2>
      {summary.reason ? <p>{summary.reason}</p> : null}
      {report ? <>
        <p>Run <time dateTime={report.generated_at}>{new Date(report.generated_at).toLocaleString()}</time>.
          {" "}Offline engineering checks replay saved fake and curated responses.
          They measure checker regressions, not fresh model accuracy.</p>
        <p><strong>Model accuracy: unavailable.</strong> All {report.draft_chunks} public fact chunks
          remain drafts. Citation membership does not prove semantic support.
          Curated fit examples are not calibrated ground truth.</p>
        <h2>Recorded response checks</h2>
        <table><caption>Saved responses by category</caption>
          <thead><tr><th scope="col">Category</th><th scope="col">Passed / total</th><th scope="col">Skipped</th></tr></thead>
          <tbody>{report.categories.map((row) => <tr key={row.category}>
            <th scope="row">{row.category}</th><td>{row.passed} / {row.total}</td><td>{row.skipped}</td>
          </tr>)}</tbody></table>
        <p>{report.development_without_recordings} development cases have no saved response; this is incomplete development-case coverage.</p>
        <h2>Local retrieval</h2>
        <p>Hit measures whether a relevant source appears. Recall measures coverage of exhaustively
          labeled sources. MRR measures the first relevant source’s rank. Alternative-source labels
          have no recall denominator. These are retrieval metrics, not answer accuracy.</p>
        <table><caption>Development retrieval metrics</caption>
          <thead><tr><th scope="col">Suite</th><th scope="col">Metric</th><th scope="col">Value</th><th scope="col">Queries</th></tr></thead>
          <tbody>{report.retrieval.map((row) => <tr key={`${row.suite}-${row.metric}`}>
            <th scope="row">{row.suite.replaceAll("_", " ")}</th>
            <td>{row.metric.replaceAll("_", " ")}</td>
            <td>{row.denominator ? (row.numerator / row.denominator).toFixed(4) : "Unavailable"}</td>
            <td>{row.denominator}</td>
          </tr>)}</tbody></table>
        <h2>Human and judge agreement</h2>
        <p>Independent validation gate: <strong>{report.judge_validation.status}</strong>.
          {" "}The utility model ({report.judge_validation.model}) graded eight authored validation
          answers against Aamir’s frozen grades after twenty calibration examples. The models
          share a family; this is a small-sample judge reliability check, not generator accuracy.</p>
        <table><caption>Independent validation agreement (80% floor per axis)</caption>
          <thead><tr><th scope="col">Axis</th><th scope="col">Agreement</th><th scope="col">Disagreements</th></tr></thead>
          <tbody>{Object.entries(report.judge_validation.axes).map(([axis, count]) => <tr key={axis}>
            <th scope="row">{axis}</th><td>{count.passed} / {count.total} ({(count.passed / count.total * 100).toFixed(1)}%)</td>
            <td>{report.judge_validation.failures_by_axis[axis]}</td>
          </tr>)}</tbody></table>
        <ul>{report.judge_validation.disagreements.map((row) => <li key={`${row.item_id}-${row.axis}`}>
          {row.item_id}: {row.axis} — human {row.human}, judge {row.judge}
        </li>)}</ul>
        <p>All disagreements and original human grades are retained. No failed judgment was retried
          to improve a score. The failed gate remains the accepted empirical baseline.</p>
        <h2>Failures and reserved evidence</h2>
        {report.failed_checks.length ? <ul>{report.failed_checks.map((failure) => <li key={failure}>{failure}</li>)}</ul>
          : <p>No offline retrieval/replay gate failures in this artifact. The independent judge gate above failed.</p>}
        <p>{report.held_out_reserved} held-out cases remain reserved and unexecuted. Their text, IDs,
          and expected answers are not exposed here. Further judge tuning needs a fresh independent validation set.</p>
        <p>The reserved cases are author-visible, not an independently blind assessment.</p>
        <h2>Provenance</h2>
        <dl><dt>Source commit</dt><dd>{report.source_commit}{report.source_dirty ? " (working tree had changes)" : " (clean)"}</dd>
          <dt>Result SHA-256</dt><dd>{report.source_result_sha256}</dd>
          <dt>Judge validation SHA-256</dt><dd>{report.judge_validation.artifact_sha256}</dd>
          <dt>Rubric SHA-256</dt><dd>{report.judge_validation.rubric_sha256}</dd></dl>
      </> : null}
    </>}
  </main>;
}
