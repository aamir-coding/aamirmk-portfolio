import { useCallback, useEffect, useRef, useState } from "react";
import { fetchFitPresets } from "../lib/api";
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
  activePreset: SampleJobDescription | null;
  loadPreset: (preset: SampleJobDescription) => void;
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
  const [activePreset, setActivePreset] = useState<SampleJobDescription | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Load presets on mount
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    const loadPresets = async () => {
      setIsLoadingPresets(true);
      try {
        const data = await fetchFitPresets(controller.signal);
        if (isMounted) {
          setPresets(data);
        }
      } catch {
        // Silently tolerate preset load failure
      } finally {
        if (isMounted) {
          setIsLoadingPresets(false);
        }
      }
    };

    void loadPresets();

    return () => {
      isMounted = false;
      controller.abort();
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
    setActivePreset(null);
    setStatus("idle");
  }, [abort]);

  const loadPreset = useCallback(
    (preset: SampleJobDescription) => {
      abort();
      setError(null);
      setProgress(null);
      setActivePreset(preset);

      if (preset.report) {
        setReport(preset.report);
        setStatus("completed");
      }
    },
    [abort]
  );

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

      try {
        await streamFitReport({
          jdText: jdText.trim(),
          roleTitle: roleTitle?.trim() || undefined,
          signal: controller.signal,
          callbacks: {
            onProgress: (p) => {
              setProgress(p);
            },
            onComplete: (rep) => {
              setReport(rep);
              setStatus("completed");
              setProgress(null);
            },
            onError: (err) => {
              setError(err || "An error occurred during fit evaluation.");
              setStatus("error");
              setProgress(null);
            },
          },
        });
      } catch (err: unknown) {
        if (controller.signal.aborted) {
          // Intentionally aborted
          return;
        }
        const message = err instanceof Error ? err.message : "Fit evaluation failed";
        setError(message);
        setStatus("error");
        setProgress(null);
      } finally {
        abortControllerRef.current = null;
      }
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
    activePreset,
    loadPreset,
    submit,
    abort,
    reset,
  };
}
