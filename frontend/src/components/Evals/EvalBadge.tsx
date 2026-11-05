import "../../styles/evals.css";
import { useEvalSummary } from "../../lib/evals";

export function EvalBadge() {
  const { summary, error } = useEvalSummary();
  return <a className="eval-badge" href="/evals">
    {summary?.badge ?? (error ? "Evaluation results unavailable" : "Evaluation results")}
  </a>;
}
