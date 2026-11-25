import { lazy, Suspense, useCallback, useEffect, useLayoutEffect, useRef, useState, type MouseEvent } from "react";
import { EvalBadge } from "./components/Evals/EvalBadge";
import { AssistantFallback } from "./components/AssistantFallback";
import { useServerHealth } from "./hooks/useServerHealth";
import { useChat } from "./hooks/useChat";
import { useCompanyContext } from "./hooks/useCompanyContext";
import { useTheme } from "./hooks/useTheme";
import { ChatInput } from "./components/Chat/ChatInput";
import { ConversationRibbon, type RibbonSend } from "./components/Chat/ConversationRibbon";
import { StarterChips } from "./components/Chat/StarterChips";
import { CoverState } from "./components/Cover/CoverState";
import { HeroArt } from "./components/Cover/HeroArt";
import { SelectedWork } from "./components/Cover/SelectedWork";
import { projects, type ShowcaseId } from "./components/Cover/projects";
import { SidePanel } from "./components/Cover/SidePanel";
import { useArtPreferences } from "./hooks/useArtPreferences";
import { ThemeToggle } from "./components/ThemeToggle";
import {
  StatusIndicator,
} from "./components/StatusIndicator";
import { FitReportModal } from "./components/Fit/FitReportModal";
import { SummaryAction } from "./components/Summary/SummaryAction";
import answersData from "./data/answers.json";
import type { InstantAnswer, ProjectCardData } from "./lib/types";
import { summaryProjectIds } from "./lib/summary";
import "./styles/chat.css";
import "./styles/portfolio.css";
import "./styles/fit.css";

const BUNDLED_ANSWERS = answersData as Record<string, InstantAnswer>;
const FEATURED_PROMPT = "What did Aamir build at AlgoUniversity?";

const loadTranscript = () => import("./components/Chat/MessageList").then(module => ({ default: module.MessageList }));
const MessageList = lazy(loadTranscript);
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
  const { preferences, set, cue } = useArtPreferences();
  const [evidenceCard, setEvidenceCard] = useState<ProjectCardData>();
  const [panel, setPanel] = useState<"index" | "preferences" | ShowcaseId | null>(null);
  useEffect(() => {
    const routes: Record<string, ShowcaseId | "index"> = {
      "#work": "index", "#entropy": "entropy-oj", "#portfolio-assistant": "ai-digital-assistant", "#health-tracker": "health-tracker",
    };
    const navigate = () => setPanel(routes[location.hash] ?? null);
    navigate();
    window.addEventListener("hashchange", navigate);
    return () => window.removeEventListener("hashchange", navigate);
  }, []);
  const closePanel = () => {
    setPanel(null);
    if (["#work", "#entropy", "#portfolio-assistant", "#health-tracker"].includes(location.hash)) {
      history.replaceState(history.state, "", location.pathname + location.search);
    }
  };
  const inspectProject = useCallback((id: ShowcaseId, card?: ProjectCardData) => {
    cue("evidence");
    setEvidenceCard(card);
    setPanel(id);
  }, [cue]);
  const selectedProject = projects.find(project => project.id === panel);
  const assistantRef = useRef<HTMLElement>(null);
  const focusAfterNavigation = useRef(false);
  const assistantStatus = isResting ? "resting" : serverState;
  const reply = messages.at(-1);
  const [ribbonSend, setRibbonSend] = useState<RibbonSend | null>(null);
  const markSend = () => {
    cue("send");
    setRibbonSend({ at: performance.now(), river: document.querySelector(".relief-river")?.getBoundingClientRect() });
  };
  const stage = reply?.delivery === "cancelled" || reply?.status === "error" ? "stopped"
    : isStreaming ? (reply?.content ? "writing" : "waiting") : "settled";
  const soundedReply = useRef<string | null>(null);
  useEffect(() => {
    if (!ribbonSend || isCoverState || reply?.status !== "done" || reply.delivery ||
        !reply.content || (reply.browserTiming?.total_ms ?? 0) < 5000 || soundedReply.current === reply.id) return;
    soundedReply.current = reply.id;
    cue("ready");
  }, [reply, cue, ribbonSend, isCoverState]);
  let announcement = "";
  if (reply?.role === "assistant" && reply.status === "done") {
    if (reply.delivery === "cancelled") announcement = "Response stopped.";
    else if (reply.delivery === "instant") announcement = "Saved answer ready in conversation history.";
    else announcement = "Answer ready in conversation history.";
  }
  const healthNotice = assistantStatus === "warming"
    ? "The assistant is waking up. You can read a saved answer while it connects."
    : assistantStatus === "resting"
      ? "Live capacity is temporarily unavailable. Saved answers and curated role examples are available."
      : assistantStatus === "error" ? healthError : null;
  const showRecovery = Boolean(healthNotice || error);

  useLayoutEffect(() => {
    if (!focusAfterNavigation.current) return;
    focusAfterNavigation.current = false;
    headingRef.current?.focus();
  }, [isCoverState, panel]);

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

  const warmTranscript = () => { void loadTranscript().catch(() => {}); };
  const showChat = (moveFocus: boolean) => {
    if (isCoverState || panel) {
      focusAfterNavigation.current = moveFocus;
    } else if (moveFocus) {
      headingRef.current?.focus();
    }
    setViewMode("chat");
  };

  const showOverview = () => {
    focusAfterNavigation.current = true;
    setViewMode("cover");
  };

  const handleSelectPrompt = (prompt: string, useSaved = false) => {
    if (isStreaming) return;
    markSend();
    showChat(true);
    // If backend is asleep or still warming, answer instantly from bundled answers.json
    if ((useSaved || serverState !== "ready" || isResting) && BUNDLED_ANSWERS[prompt]) {
      sendInstantAnswer(prompt, BUNDLED_ANSWERS[prompt]);
      return;
    }
    void sendMessage(prompt);
  };

  const handleOpenFitModal = (event: MouseEvent<HTMLButtonElement>) => {
    event.currentTarget.focus({ preventScroll: true });
    setIsFitModalOpen(true);
  };

  const handleAskGap = (gapText: string) => {
    markSend();
    setIsFitModalOpen(false);
    showChat(true);
    void sendMessage(`How does Aamir plan to ramp up on: ${gapText}?`);
  };

  const handleResetChat = () => {
    resetChat();
    showOverview();
  };

  const restoreRecoveryFocus = (event: MouseEvent<HTMLButtonElement>) => {
    if (event.detail === 0) assistantRef.current?.focus({ preventScroll: true });
  };

  const handleRefreshHealth = (event: MouseEvent<HTMLButtonElement>) => {
    restoreRecoveryFocus(event);
    clearResting();
    refreshHealth();
  };

  return (
    <div className="portfolio-page">
      <a className="portfolio-skip" href="#main-heading">Skip to main content</a>
      <p className="sr-only" role="status">{announcement && <span key={reply?.id}>{announcement}</span>}</p>
      <header className="portfolio-bar">
        <div className="portfolio-measure portfolio-bar-inner">
          <button className="portfolio-brand" type="button" onClick={isCoverState ? () => headingRef.current?.focus() : showOverview}>
            <svg aria-hidden="true" viewBox="0 0 40 40" fill="none" stroke="currentColor" strokeWidth="1.7">
              <path d="M3 27 16 6l7 11 6-9 9 17-16 10z M5 27l11-16 7 11 6-9 6 12-13 7z M8 27l8-11 7 11 6-9 3 7-10 4z" />
            </svg>
            <span><strong>Aamir Mohammed Khan</strong><small>Digital assistant</small></span>
          </button>
          <nav className="portfolio-nav" aria-label="Portfolio">
            <button type="button" aria-haspopup="dialog" onClick={() => setPanel("index")} aria-label="Project index"><span className="nav-project-label">Project index</span><span className="nav-project-short">Projects</span></button>
            <a href="/resume.pdf" target="_blank" rel="noopener noreferrer">Résumé</a>
            <ThemeToggle theme={theme} resolvedTheme={resolvedTheme} onCycle={cycleTheme} />
            <button type="button" className="preferences-trigger" aria-label="Preferences" title="Preferences" aria-haspopup="dialog" onClick={() => setPanel("preferences")}>
              <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 7h6m5 0h7M3 17h11m5 0h2"/><circle cx="11" cy="7" r="2.5"/><circle cx="16" cy="17" r="2.5"/></svg>
            </button>
          </nav>
        </div>
      </header>

      <main>
        <div className={`portfolio-opening ${isCoverState ? "portfolio-cover" : "portfolio-conversation"}`}>
          <div className="portfolio-measure portfolio-opening-inner">
            {isCoverState && <CoverState headingRef={headingRef} company={company} />}
            {!isCoverState && <ConversationRibbon send={ribbonSend} stage={stage} graphite={resolvedTheme === "dark"} live={preferences.artwork === "metal"} />}
            <section
              ref={assistantRef}
              className="portfolio-assistant"
              id="assistant"
              aria-labelledby={isCoverState ? "assistant-heading" : "main-heading"}
              tabIndex={-1}
            >
              <div className="portfolio-assistant-heading">
                {isCoverState ? <h2 className="sr-only" id="assistant-heading">Ask about Aamir</h2> : (
                  <h1 className="sr-only" id="main-heading" ref={headingRef} tabIndex={-1}>Conversation</h1>
                )}
                <StatusIndicator state={assistantStatus} errorMessage={healthError} />
              </div>
              <div className="portfolio-chat" onFocusCapture={isCoverState ? warmTranscript : undefined}>
                {!isCoverState && (
                  <Suspense fallback={<p role="status">Opening conversation…</p>}>
                    <MessageList messages={messages} isStreaming={isStreaming} onOverview={showOverview} onClear={handleResetChat} onInspectProject={inspectProject} />
                  </Suspense>
                )}
                <div className="chat-input-container">
                  {summaryTopics && <SummaryAction projectIds={summaryTopics} />}
                  <ChatInput
                    onSend={(text) => {
                      markSend();
                      showChat(false);
                      void sendMessage(text);
                    }}
                    onStop={stopStreaming}
                    isStreaming={isStreaming}
                  />
                  <button type="button" className="role-fit-action" onClick={handleOpenFitModal} aria-haspopup="dialog">
                    <svg aria-hidden="true" viewBox="0 0 20 20" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <rect x="2" y="6" width="16" height="11" rx="2" />
                      <path d="M7 6V4.5A1.5 1.5 0 0 1 8.5 3h3A1.5 1.5 0 0 1 13 4.5V6M2 10q8 4 16 0" />
                    </svg>
                    Check role fit
                  </button>
                </div>
              </div>

              {isCoverState && messages.length > 0 && <button className="text-action" onClick={() => showChat(true)}>Resume chat</button>}
              {showRecovery && (
                <div className="portfolio-notice">
                  <p role={error ? "alert" : undefined}>{error || healthNotice}</p>
                  <div className="portfolio-recovery-actions">
                    <button className="saved-answer-action" type="button" disabled={isStreaming} onClick={() => handleSelectPrompt(FEATURED_PROMPT, true)}>
                      Read a saved answer
                    </button>
                    {(assistantStatus === "resting" || assistantStatus === "error") &&
                      <button className="service-action" type="button" onClick={handleRefreshHealth}>Check service status</button>}
                    {error && <button type="button" onClick={event => {
                      restoreRecoveryFocus(event);
                      clearError();
                    }}>Dismiss</button>}
                  </div>
                  <AssistantFallback />
                </div>
              )}
            </section>
            {isCoverState && <HeroArt artwork={preferences.artwork} />}
          </div>
        </div>

        {isCoverState && <section className="portfolio-measure starting-questions" aria-labelledby="starter-title">
          <h2 id="starter-title">Start with a question</h2>
          <div className="project-questions">
            {projects.map(project => <button key={project.id} disabled={isStreaming} onClick={() => handleSelectPrompt(project.question)}>
              <img src={project.mobile} alt="" width="64" height="45" />
              <span>{project.question}</span><span aria-hidden="true">→</span>
            </button>)}
          </div>
          <details open={company ? true : undefined}>
            <summary>More questions to ask</summary>
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
          </details>
        </section>}
      </main>

      <footer className="portfolio-footer">
        <div className="portfolio-measure portfolio-footer-inner">
          <section aria-labelledby="portfolio-contact">
            <h2 id="portfolio-contact">Contact Aamir</h2>
            <nav className="portfolio-contact-links" aria-label="Direct candidate links">
              <a href="mailto:aamirmkh25@gmail.com">Email Aamir</a>
              <a href="https://www.linkedin.com/in/aamir-mk/" target="_blank" rel="noopener noreferrer">LinkedIn</a>
              <a href="https://github.com/aamir-coding" target="_blank" rel="noopener noreferrer">GitHub</a>
            </nav>
          </section>
          <div className="portfolio-footer-notes">
            <div className="portfolio-utilities">
              <EvalBadge />
            </div>
            <details>
              <summary>Privacy and data use</summary>
              <p>Groq processes live questions and job descriptions. This browser tab stores a copy of the chat. Fit reports are reused for up to 15 minutes and held in bounded server memory until eviction or restart.</p>
              <p>When analytics is enabled, the service stores questions, usage, basic visit details, and feedback to improve the portfolio. Analytics and handoff records are removed in daily cleanup after 90 days. Service logs record only operational metadata, including request IDs and temporary salted IP hashes.</p>
              <p>Handoffs you approve are sent to Aamir on Telegram, which keeps its own copy. Summary links expire after 30 days.</p>
            </details>
          </div>
        </div>
      </footer>
      {panel && <SidePanel title={selectedProject?.title ?? (panel === "preferences" ? "Preferences" : "Project index")} onClose={closePanel}>
        {panel === "preferences" ? <div className="art-settings">
          <label>Interaction sounds<input type="checkbox" checked={preferences.sound} onChange={e => set("sound", e.target.checked)} /></label>
          <label>Landscape<select value={preferences.artwork} onChange={e => {
            const value = e.currentTarget.value;
            if (value === "metal" || value === "reflection" || value === "still") set("artwork", value);
          }}>
            <option value="metal">Liquid metal river</option><option value="reflection">Still river reflection</option><option value="still">Still landscape</option>
          </select></label>
        </div> : <>
          {selectedProject && <button className="text-action" onClick={() => setPanel("index")}>Back to project index</button>}
          <SelectedWork projectId={selectedProject?.id} card={selectedProject?.id === evidenceCard?.id ? evidenceCard : undefined} onSelect={inspectProject} disabled={isStreaming}
            onAsk={question => { closePanel(); handleSelectPrompt(question); }}
            onSample={() => { closePanel(); handleSelectPrompt(FEATURED_PROMPT, true); }} />
        </>}
      </SidePanel>}
      {isFitModalOpen && (
        <FitReportModal
          isOpen={isFitModalOpen}
          onClose={() => setIsFitModalOpen(false)}
          onAskGap={isStreaming ? undefined : handleAskGap}
        />
      )}
    </div>
  );
}

export default App;
