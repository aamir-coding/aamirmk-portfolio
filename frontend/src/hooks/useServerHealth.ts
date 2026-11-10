import { useCallback, useEffect, useState } from "react";
import { fetchHealth } from "../lib/api";
import type { ServerState } from "../components/StatusIndicator";

export function useServerHealth() {
  const [state, setState] = useState<ServerState>("checking");
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  const refresh = useCallback(() => {
    setState("checking");
    setError(null);
    setAttempt(n => n + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const warming = setTimeout(() => setState("warming"), 2500);
    const deadline = setTimeout(() => {
      controller.abort();
      clearTimeout(warming);
      setState("error");
      setError("The assistant service has not responded yet. Starter inquiries and the résumé are available.");
    }, 90000);

    void fetchHealth(controller.signal).then(health => {
      if (controller.signal.aborted) return;
      setState(health.assistant_state === "ready" ? "ready" : "resting");
      setError(null);
    }).catch(() => {
      if (controller.signal.aborted) return;
      setState("error");
      setError("The assistant service is unavailable. Starter inquiries and the résumé are available.");
    }).finally(() => {
      clearTimeout(warming);
      clearTimeout(deadline);
    });

    return () => {
      controller.abort();
      clearTimeout(warming);
      clearTimeout(deadline);
    };
  }, [attempt]);

  return { state, error, refresh };
}
