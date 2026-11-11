export function AssistantFallback() {
  return <div className="assistant-fallback" role="group" aria-label="Alternatives to live answers">
    <a href="/resume.pdf" target="_blank" rel="noopener noreferrer">Résumé (PDF)</a>
    {" · "}
    <a href="https://www.linkedin.com/in/aamir-mk/"
      target="_blank" rel="noopener noreferrer">View professional profile</a>
    {" · "}<a href="mailto:aamirmkh25@gmail.com">Contact Aamir</a>
  </div>;
}
