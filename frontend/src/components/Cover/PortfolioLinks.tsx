import { EvalBadge } from "../Evals/EvalBadge";

export function PortfolioLinks() {
  return <>
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
  </>;
}
