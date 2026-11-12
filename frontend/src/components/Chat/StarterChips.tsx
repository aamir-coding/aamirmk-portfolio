export interface StarterChipsProps {
  onSelect: (prompt: string) => void;
  onOpenFitModal?: () => void;
  disabled?: boolean;
  prompts?: readonly string[];
}

const STARTER_PROMPTS = [
  "What is Aamir's experience with FastAPI and LLM systems?",
  "Tell me about his key projects and production impact.",
  "What are Aamir's core technical strengths?",
  "What role is Aamir looking for?",
];

export function StarterChips({
  onSelect,
  onOpenFitModal,
  disabled = false,
  prompts = STARTER_PROMPTS,
}: StarterChipsProps) {
  return (
    <div className="starter-chips-container" role="group" aria-label="Suggested starter questions">
      <span className="starter-chips-label">Suggested Inquiries</span>
      <div className="starter-chips-grid">
        {onOpenFitModal && (
          <button
            type="button"
            className="starter-chip starter-chip-accent"
            onClick={onOpenFitModal}
            disabled={disabled}
            aria-label="Open Job Description Fit Report dialog"
          >
            ⚡ Check Role Fit (Paste JD)
          </button>
        )}
        {prompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="starter-chip"
            onClick={() => onSelect(prompt)}
            disabled={disabled}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
