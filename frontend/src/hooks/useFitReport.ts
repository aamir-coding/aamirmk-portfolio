import { useCallback, useEffect, useRef, useState } from "react";
import { getApiBaseUrl } from "../lib/api";
import { streamFitReport } from "../lib/sse";
import type { FitProgressData, FitReport, SampleJobDescription } from "../lib/types";

export type FitStatus = "idle" | "streaming" | "completed" | "error";

export interface UseFitReportReturn {
  status: FitStatus;
  progress: FitProgressData | null;
  report: FitReport | null;
  error: string | null;
  presets: SampleJobDescription[];
  isLoadingPresets: boolean;
  submit: (jdText: string, roleTitle?: string) => Promise<void>;
  abort: () => void;
  reset: () => void;
}

export function useFitReport(): UseFitReportReturn {
  const [status, setStatus] = useState<FitStatus>("idle");
  const [progress, setProgress] = useState<FitProgressData | null>(null);
  const [report, setReport] = useState<FitReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<SampleJobDescription[]>([]);
  const [isLoadingPresets, setIsLoadingPresets] = useState<boolean>(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Load presets on mount
  useEffect(() => {
    let isMounted = true;
    const fetchPresets = async () => {
      setIsLoadingPresets(true);
      try {
        const res = await fetch(`${getApiBaseUrl()}/api/fit/presets`);
        if (res.ok) {
          const data = await res.json();
          if (isMounted && Array.isArray(data)) {
            setPresets(data);
          }
        }
      } catch {
        // Silently tolerate preset load failure
      } finally {
        if (isMounted) {
          setIsLoadingPresets(false);
        }
      }
    };

    fetchPresets();
    return () => {
      isMounted = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus("idle");
    setProgress(null);
  }, []);

  const reset = useCallback(() => {
    abort();
    setReport(null);
    setError(null);
    setProgress(null);
    setStatus("idle");
  }, [abort]);

  const submit = useCallback(
    async (jdText: string, roleTitle?: string) => {
      if (!jdText.trim() || jdText.trim().length < 50) {
        setError("Please provide a job description of at least 50 characters.");
        setStatus("error");
        return;
      }

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setStatus("streaming");
      setError(null);
      setReport(null);
      setProgress({
        step: "init",
        message: "Connecting to verification engine...",
        percent: 0,
      });

      await streamFitReport({
        jdText: jdText.trim(),
        roleTitle: roleTitle?.trim(),
        signal: controller.signal,
        callbacks: {
          onProgress: (p) => {
            setProgress(p);
          },
          onComplete: (r) => {
            setReport(r);
            setStatus("completed");
            setProgress(null);
            abortControllerRef.current = null;
          },
          onError: (errMsg) => {
            setError(errMsg);
            setStatus("error");
            setProgress(null);
            abortControllerRef.current = null;
          },
        },
      });
    },
    []
  );

  return {
    status,
    progress,
    report,
    error,
    presets,
    isLoadingPresets,
    submit,
    abort,
    reset,
  };
}
