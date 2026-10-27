export interface StarterChipsProps {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

const STARTER_PROMPTS = [
  "What is Aamir's experience with FastAPI and LLM systems?",
  "Tell me about his key projects and production impact.",
  "What are Aamir's core technical strengths?",
  "What role is Aamir looking for?",
];

export function StarterChips({ onSelect, disabled = false }: StarterChipsProps) {
  return (
    <div className="starter-chips-container" aria-label="Suggested starter questions">
      <span className="starter-chips-label">Suggested Inquiries</span>
      <div className="starter-chips-grid">
        {STARTER_PROMPTS.map((prompt) => (
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
