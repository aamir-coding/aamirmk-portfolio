import { lazy, Suspense, useState } from "react";
import { EvalBadge } from "./components/Evals/EvalBadge";
import { AssistantFallback } from "./components/AssistantFallback";
import { useServerHealth } from "./hooks/useServerHealth";
import { useChat } from "./hooks/useChat";
import { useCompanyContext } from "./hooks/useCompanyContext";
import { useTheme } from "./hooks/useTheme";
import { MessageList } from "./components/Chat/MessageList";
import { ChatInput } from "./components/Chat/ChatInput";
import { ThemeToggle } from "./components/ThemeToggle";
import {
  StatusIndicator,
} from "./components/StatusIndicator";
import { FitReportModal } from "./components/Fit/FitReportModal";
import { SummaryAction } from "./components/Summary/SummaryAction";
import answersData from "./data/answers.json";
import type { InstantAnswer } from "./lib/types";
import { summaryProjectIds } from "./lib/summary";
import "./styles/chat.css";

const BUNDLED_ANSWERS = answersData as Record<string, InstantAnswer>;

const EvalPage = lazy(() => import("./components/Evals/EvalPage"));
const AdminPage = lazy(() => import("./components/Admin/AdminPage"));
const SummaryPage = lazy(() => import("./components/Summary/SummaryPage"));

export function App() {
  const path = window.location.pathname.replace(/\/$/, "");
  if (path === "/s" || path.startsWith("/s/")) {
    const token = path.slice(3);
    return (
      <>
        <meta name="robots" content="noindex, nofollow" />
        <meta name="referrer" content="no-referrer" />
        <Suspense fallback={<p role="status">Loading team summary…</p>}>
          <SummaryPage key={token} token={token} />
        </Suspense>
      </>
    );
  }
  if (path === "/admin") {
    return <Suspense fallback={<p role="status">Loading dashboard…</p>}><AdminPage /></Suspense>;
  }
  return path === "/evals"
    ? <Suspense fallback={<p role="status">Loading evaluation record…</p>}><EvalPage /></Suspense>
    : <Portfolio />;
}

function Portfolio() {
  const company = useCompanyContext(new URLSearchParams(window.location.search).get("for"));
  const { state: serverState, error: healthError, refresh: refreshHealth } = useServerHealth();
  const [isFitModalOpen, setIsFitModalOpen] = useState(false);
  const { theme, resolvedTheme, cycleTheme } = useTheme();

  const {
    messages,
    isStreaming,
    error,
    isResting,
    clearResting,
    sendMessage,
    sendInstantAnswer,
    stopStreaming,
    clearError,
    resetChat,
  } = useChat(company?.slug);

  // If restoring chat from sessionStorage on mount, automatically open in chat view
  const [viewMode, setViewMode] = useState<"cover" | "chat">(() =>
    messages.length > 0 ? "chat" : "cover"
  );

  const isCoverState = viewMode === "cover" || messages.length === 0;
  const completedReplies = isCoverState ? [] : messages.filter(message =>
    message.role === "assistant" && message.status === "done" &&
    message.delivery !== "cancelled" && message.content.trim()
  );
  const summaryTopics = completedReplies.length >= 2 ? summaryProjectIds(
    completedReplies.slice(-4).reverse().flatMap(message => [
      ...(message.cards ?? []).map(card => card.id),
      ...(message.sources ?? []).map(source => source.chunk_id),
    ]),
  ) : null;

  const handleSelectPrompt = (prompt: string) => {
    setViewMode("chat");
    // If backend is asleep or still warming, answer instantly from bundled answers.json
    if ((serverState !== "ready" || isResting) && BUNDLED_ANSWERS[prompt]) {
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

  const handleRefreshHealth = () => {
    clearResting();
    refreshHealth();
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-title-group">
          <h1>Aamir Mohammed Khan</h1>
          <p>AI Digital Assistant — Conversational Portfolio</p>
        </div>
        <div className="header-controls">
          <EvalBadge />
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
          <StatusIndicator state={isResting ? "resting" : serverState} errorMessage={healthError} />
        </div>
      </header>

      {(serverState === "resting" || isResting) && <div className="banner-notice warning" role="status" aria-live="polite">
        <div><p>Live answers are resting. Starter inquiries and curated role examples remain available.</p>
          <AssistantFallback /></div>
      </div>}

      {(serverState === "resting" || isResting || serverState === "error") && <div className="banner-notice warning" role="status">
        <div>{healthError && <p>{healthError}</p>}
          {serverState === "error" && <AssistantFallback />}
          <button type="button" className="btn btn-secondary" onClick={handleRefreshHealth}>Check service status</button>
        </div>
      </div>}

      {serverState === "warming" && (
        <div
          className="banner-notice warning"
          role="status"
          aria-live="polite"
        >
          <span>
            <strong>The assistant service is waking up.</strong> Saved answers
            are available while it connects. You can also view Aamir's résumé
            or contact him directly.
          </span>
          <AssistantFallback />
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
            company={company}
            onSelectPrompt={handleSelectPrompt}
            onOpenFitModal={handleOpenFitModal}
          />
        </div>

        <div className="chat-input-container">
          {summaryTopics && <SummaryAction projectIds={summaryTopics} />}
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

      <footer className="fit-form-notice">
        <p>AI assistant about Aamir. Groq processes live questions and job descriptions.
          This browser tab stores a copy of the chat. When analytics is enabled, the service
          stores questions, usage, basic visit details, and feedback to improve the portfolio.
          Analytics and handoff records are removed in daily cleanup after 90 days.
          Handoffs you approve are sent to Aamir on Telegram, which keeps its own copy.
          Summary links expire after 30 days. Reports are reused for up to 15 minutes and
          held in bounded server memory until eviction or restart.
          Service logs record only operational metadata, including request IDs and temporary salted IP hashes.</p>
      </footer>

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
