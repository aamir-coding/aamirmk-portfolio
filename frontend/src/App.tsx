import { useEffect, useState } from "react";
import { fetchHealth } from "./lib/api";
import { useChat } from "./hooks/useChat";
import { useTheme } from "./hooks/useTheme";
import { MessageList } from "./components/Chat/MessageList";
import { ChatInput } from "./components/Chat/ChatInput";
import { ThemeToggle } from "./components/ThemeToggle";
import {
  StatusIndicator,
  type ServerState,
} from "./components/StatusIndicator";
import { FitReportModal } from "./components/Fit/FitReportModal";
import answersData from "./data/answers.json";
import type { InstantAnswer } from "./lib/types";
import "./styles/chat.css";

const BUNDLED_ANSWERS = answersData as Record<string, InstantAnswer>;

export function App() {
  const [serverState, setServerState] = useState<ServerState>("checking");
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isFitModalOpen, setIsFitModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"cover" | "chat">("cover");
  const { theme, resolvedTheme, cycleTheme } = useTheme();

  const {
    messages,
    isStreaming,
    error,
    sendMessage,
    sendInstantAnswer,
    stopStreaming,
    clearError,
    resetChat,
  } = useChat();

  // If restoring chat from sessionStorage on mount, automatically open in chat view
  useEffect(() => {
    if (messages.length > 0) {
      setViewMode("chat");
    }
  }, []);

  const isCoverState = viewMode === "cover" || messages.length === 0;

  useEffect(() => {
    const controller = new AbortController();

    // If health check takes > 2.5s, signal to the user that Render is warming up
    const warmingTimer = setTimeout(() => {
      setServerState("warming");
    }, 2500);

    async function checkBackend() {
      try {
        await fetchHealth(controller.signal);
        clearTimeout(warmingTimer);
        setServerState("ready");
        setHealthError(null);
      } catch (err) {
        if (!controller.signal.aborted) {
          clearTimeout(warmingTimer);
          setServerState("error");
          setHealthError(
            err instanceof Error ? err.message : "Failed to connect to backend"
          );
        }
      }
    }

    void checkBackend();

    return () => {
      clearTimeout(warmingTimer);
      controller.abort();
    };
  }, []);

  const handleSelectPrompt = (prompt: string) => {
    setViewMode("chat");
    // If backend is asleep or still warming, answer instantly from bundled answers.json
    if (serverState !== "ready" && BUNDLED_ANSWERS[prompt]) {
      sendInstantAnswer(prompt, BUNDLED_ANSWERS[prompt]);
      return;
    }
    void sendMessage(prompt);
  };

  const handleOpenFitModal = () => {
    setIsFitModalOpen(true);
  };

  const handleAskGap = (gapText: string) => {
    setIsFitModalOpen(false);
    setViewMode("chat");
    void sendMessage(`How does Aamir plan to ramp up on: ${gapText}?`);
  };

  const handleResetChat = () => {
    resetChat();
    setViewMode("cover");
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-title-group">
          <h1>Aamir Mohammed Khan</h1>
          <p>AI Digital Assistant — Conversational Portfolio</p>
        </div>
        <div className="header-controls">
          <button
            type="button"
            className="btn-header-fit"
            onClick={handleOpenFitModal}
            aria-label="Evaluate Job Description Alignment"
          >
            ⚡ Role Fit
          </button>
          {isCoverState && messages.length > 0 && (
            <button
              type="button"
              className="btn-header-resume"
              onClick={() => setViewMode("chat")}
              aria-label="Resume active chat conversation"
            >
              Resume Chat ({messages.length}) →
            </button>
          )}
          {!isCoverState && (
            <>
              <button
                type="button"
                className="btn-header-dossier"
                onClick={() => setViewMode("cover")}
                aria-label="Return to candidate dossier overview"
              >
                ← Dossier Overview
              </button>
              <button
                type="button"
                className="btn-header-reset"
                onClick={handleResetChat}
                disabled={isStreaming}
                aria-label="Clear active conversation and reset"
                title="Clear conversation"
              >
                Clear Chat
              </button>
            </>
          )}
          <ThemeToggle
            theme={theme}
            resolvedTheme={resolvedTheme}
            onCycle={cycleTheme}
          />
          <StatusIndicator state={serverState} errorMessage={healthError} />
        </div>
      </header>

      {serverState === "warming" && (
        <div
          className="banner-notice warning"
          role="status"
          aria-live="polite"
        >
          <span>
            <strong>Render free tier notice:</strong> Backend is cold starting
            from idle. This typically takes ~25s on the initial request.
            Starter inquiries answer instantly while waking.
          </span>
        </div>
      )}

      {error && (
        <div
          className="banner-notice warning"
          role="alert"
          style={{ cursor: "pointer" }}
          onClick={clearError}
          title="Click to dismiss"
        >
          <span>
            <strong>Notice:</strong> {error}
          </span>
          <button
            type="button"
            className="btn btn-secondary"
            style={{
              minHeight: "auto",
              padding: "0.2rem 0.5rem",
              fontSize: "0.75rem",
            }}
            onClick={clearError}
          >
            Dismiss
          </button>
        </div>
      )}

      <main
        className={`chat-shell ${isCoverState ? "mode-cover" : "mode-transcript"}`}
      >
        <div className="chat-content">
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            isCoverState={isCoverState}
            onSelectPrompt={handleSelectPrompt}
            onOpenFitModal={handleOpenFitModal}
          />
        </div>

        <div className="chat-input-container">
          <ChatInput
            onSend={(text) => {
              setViewMode("chat");
              void sendMessage(text);
            }}
            onStop={stopStreaming}
            isStreaming={isStreaming}
          />
        </div>
      </main>

      {isFitModalOpen && (
        <FitReportModal
          isOpen={isFitModalOpen}
          onClose={() => setIsFitModalOpen(false)}
          onAskGap={handleAskGap}
        />
      )}
    </div>
  );
}

export default App;
