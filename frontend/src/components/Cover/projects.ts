import entropy from "./art/entropy-workspace.webp";
import entropyMobile from "./art/entropy-workspace-mobile.webp";
import assistant from "./art/assistant-saved-answer.webp";
import assistantMobile from "./art/assistant-answer-mobile.webp";
import health from "./art/healthtracker-demo.webp";

export const projects = [
  {
    id: "entropy-oj", title: "Entropy Online Judge", image: entropy, mobile: entropyMobile,
    alt: "Entropy’s Two Sum coding workspace", question: "What did Aamir build at AlgoUniversity?",
    description: "During his AlgoUniversity externship, Aamir built a coding workspace and asynchronous C++ and Python judging. Each submission runs in its own workspace with time, output, and resource limits.",
    demo: "https://entropy-oj.vercel.app/", demoLabel: "Open Entropy Online Judge", source: "https://github.com/aamir-coding/entropy-oj",
  },
  {
    id: "ai-digital-assistant", title: "AI Digital Assistant", image: assistant, mobile: assistantMobile,
    alt: "An assistant answer about Entropy with its supporting sources", question: "How does this assistant find evidence?",
    description: "Aamir built this recruiter assistant to search curated facts with BM25 and embeddings, stream answers with citations, and display project cards through validated tool calls.",
    demo: "/evals", demoLabel: "Read the assistant’s evaluation record", source: "https://github.com/aamir-coding/aamirmk-portfolio",
  },
  {
    id: "health-tracker", title: "HealthTracker", image: health, mobile: health,
    alt: "HealthTracker’s demo dashboard", question: "What went into HealthTracker?",
    description: "Aamir built a progressive web app for tracking nutrition, workouts, and health metrics, with interactive dashboards and cache-first data access.",
    demo: "https://health-tracker-alpha-one.vercel.app/", demoLabel: "Open HealthTracker", source: "https://github.com/aamir-coding/health-tracker",
  },
] as const;

export type ShowcaseId = typeof projects[number]["id"];
