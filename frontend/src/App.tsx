import { lazy, Suspense, useLayoutEffect, useRef, useState } from "react";
import { EvalBadge } from "./components/Evals/EvalBadge";
import { AssistantFallback } from "./components/AssistantFallback";
import { useServerHealth } from "./hooks/useServerHealth";
import { useChat } from "./hooks/useChat";
import { useCompanyContext } from "./hooks/useCompanyContext";
import { useTheme } from "./hooks/useTheme";
import { MessageList } from "./components/Chat/MessageList";
import { ChatInput } from "./components/Chat/ChatInput";
import { StarterChips } from "./components/Chat/StarterChips";
import { CoverState } from "./components/Cover/CoverState";
import { HeroArt } from "./components/Cover/HeroArt";
import { CandidateDetails, SelectedWork } from "./components/Cover/SelectedWork";
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
import "./styles/portfolio.css";

const BUNDLED_ANSWERS = answersData as Record<string, InstantAnswer>;
const FEATURED_PROMPT = "What did Aamir build at AlgoUniversity?";

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
  const headingRef = useRef<HTMLHeadingElement>(null);
  const focusAfterNavigation = useRef(false);
  const assistantStatus = isResting ? "resting" : serverState;

  useLayoutEffect(() => {
    if (!focusAfterNavigation.current) return;
    focusAfterNavigation.current = false;
    headingRef.current?.focus();
  }, [isCoverState]);

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

  const showChat = (moveFocus: boolean) => {
    if (isCoverState) {
      focusAfterNavigation.current = true;
    } else if (moveFocus) {
      headingRef.current?.focus();
    }
    setViewMode("chat");
  };

  const showOverview = () => {
    focusAfterNavigation.current = true;
    setViewMode("cover");
  };

  const handleSelectPrompt = (prompt: string) => {
    if (isStreaming) return;
    showChat(true);
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
    showChat(true);
    void sendMessage(`How does Aamir plan to ramp up on: ${gapText}?`);
  };

  const handleResetChat = () => {
    resetChat();
    showOverview();
  };

  const handleRefreshHealth = () => {
    clearResting();
    refreshHealth();
  };

  return (
    <div className="portfolio-page">
      <a className="portfolio-skip" href="#main-heading">Skip to main content</a>
      <header className="portfolio-bar">
        <div className="portfolio-measure portfolio-bar-inner">
          {isCoverState
            ? <a className="portfolio-brand" href="#main-heading">Aamir Mohammed Khan</a>
            : <button className="portfolio-brand" type="button" onClick={showOverview}>Aamir Mohammed Khan</button>}
          <nav className="portfolio-nav" aria-label="Portfolio">
            <a href="#assistant">Assistant</a>
            <a href="#work">Selected work</a>
            <a href="/resume.pdf" target="_blank" rel="noopener noreferrer">Résumé</a>
            <button type="button" onClick={handleOpenFitModal} aria-label="Role fit — Evaluate Job Description Alignment">
              Role fit
            </button>
          </nav>
        </div>
      </header>

      <main>
        <div className={`portfolio-opening ${isCoverState ? "portfolio-cover" : "portfolio-conversation"}`}>
          {isCoverState && <HeroArt />}
          <div className="portfolio-measure portfolio-opening-inner">
            {isCoverState && <CoverState headingRef={headingRef} company={company} />}
            <section className="portfolio-assistant" id="assistant" tabIndex={-1}>
              <div className="portfolio-assistant-heading">
                {isCoverState ? <h2>Ask about Aamir</h2> : (
                  <h1 id="main-heading" ref={headingRef} tabIndex={-1}>Conversation</h1>
                )}
                <StatusIndicator state={assistantStatus} errorMessage={healthError} />
              </div>
              {isCoverState && (
                <p className="portfolio-assistant-intro">
                  I’m an AI assistant trained on Aamir’s verified résumé, projects, and experience.
                </p>
              )}
              {!isCoverState && (
                <div className="portfolio-transcript-actions">
                  <button type="button" onClick={showOverview}>
                    Portfolio overview
                  </button>
                  <button type="button" onClick={handleResetChat} disabled={isStreaming}>
                    Clear chat
                  </button>
                </div>
              )}

              <div className="portfolio-chat">
                {!isCoverState && <MessageList messages={messages} />}
                <div className="chat-input-container">
                  {summaryTopics && <SummaryAction projectIds={summaryTopics} />}
                  <ChatInput
                    onSend={(text) => {
                      showChat(false);
                      void sendMessage(text);
                    }}
                    onStop={stopStreaming}
                    isStreaming={isStreaming}
                  />
                </div>
              </div>

              {isCoverState && (
                <div className="portfolio-starter">
                  <button type="button" onClick={() => handleSelectPrompt(FEATURED_PROMPT)} disabled={isStreaming}>
                    {FEATURED_PROMPT}<span aria-hidden="true">↗</span>
                  </button>
                  {messages.length > 0 && (
                    <button type="button" onClick={() => showChat(true)}>
                      Resume chat
                    </button>
                  )}
                </div>
              )}

              {assistantStatus === "warming" && (
                <div className="portfolio-notice">
                  <p role="status">The assistant is waking up. Saved answers are available while it connects.</p>
                  <AssistantFallback />
                </div>
              )}
              {(assistantStatus === "resting" || assistantStatus === "error") && (
                <div className="portfolio-notice">
                  <p role="status">
                    {assistantStatus === "resting"
                      ? "Live answers are resting. Saved answers and curated role examples are available."
                      : healthError}
                  </p>
                  <AssistantFallback />
                  <button type="button" onClick={handleRefreshHealth}>Check service status</button>
                </div>
              )}
              {error && (
                <div className="portfolio-notice portfolio-chat-error">
                  <p role="alert">{error}</p>
                  <button type="button" onClick={clearError}>Dismiss</button>
                </div>
              )}
            </section>
          </div>
        </div>

        <SelectedWork />
        <div className="portfolio-measure portfolio-more">
          <section className="portfolio-questions">
            <h2>More questions to ask</h2>
            {company && (
              <div className="starter-chips-container" role="group" aria-label="Highlighted projects">
                <p>{company.why_us}</p>
                <div className="starter-chips-grid">
                  {company.highlighted_projects.map(project => (
                    <button
                      key={project.id}
                      type="button"
                      className="starter-chip"
                      disabled={isStreaming}
                      onClick={() => handleSelectPrompt(`Show me the ${project.title} project.`)}
                    >
                      {project.title}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <StarterChips
              prompts={company?.suggested_questions}
              onSelect={handleSelectPrompt}
              disabled={isStreaming}
            />
          </section>
          <CandidateDetails />
        </div>
      </main>

      <footer className="portfolio-footer portfolio-measure">
        <div className="portfolio-utilities">
          <EvalBadge />
          <ThemeToggle theme={theme} resolvedTheme={resolvedTheme} onCycle={cycleTheme} />
        </div>
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
