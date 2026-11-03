/**
 * Markdown sanitization and safe link helpers for the chat message renderer.
 */

/**
 * Normalizes URLs and emails to ensure absolute protocols.
 * Guarantees external links never resolve as relative browser paths.
 */
export function formatSafeHref(rawHref?: string): string | undefined {
  if (!rawHref) return undefined;
  const trimmed = rawHref.trim();
  if (!trimmed) return undefined;

  // 1. Pass valid absolute web, mail, or tel protocols directly
  if (/^(https?:\/\/|mailto:|tel:)/i.test(trimmed)) {
    return trimmed;
  }

  // 2. Email autolink without mailto: scheme
  if (/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(trimmed)) {
    return `mailto:${trimmed}`;
  }

  // 3. Normalize common LLM protocol omission typos (e.g. "https.domain" or "httpsamirmk")
  let cleaned = trimmed.replace(/^https?\./i, "");
  if (/^https[a-zA-Z0-9-]+\.[a-zA-Z]/i.test(cleaned)) {
    cleaned = cleaned.replace(/^https/i, "");
  }

  // Prepend https:// so the browser never resolves external links relative to site root
  return `https://${cleaned}`;
}

/**
 * Safely sanitizes markdown content prior to AST generation.
 * Handles Unicode whitespace, non-breaking hyphens, glued list numerals,
 * and repairs unclosed bold contact headers without mutating domain names.
 */
export function sanitizeMarkdown(text: string): string {
  if (!text) return "";
  return (
    text
      // 1. Normalize Unicode non-breaking and zero-width spaces
      .replace(/\u202f/g, " ")
      .replace(/\u00a0/g, " ")
      .replace(/\u200b/g, "")
      // 2. Normalize Unicode non-breaking hyphen to standard ASCII hyphen
      .replace(/\u2011/g, "-")
      // 3. Separate glued list numerals (e.g., "are1. " -> "are\n\n1. ")
      .replace(/([a-zA-Z,:]|[’']s)(\d+\.\s+)/g, "$1\n\n$2")
      // 4. Safely repair unclosed bold contact headers ONLY when no closing ** exists on the line
      .replace(
        /^(\s*(?:[-*]\s+)?\*\*(?:Email|LinkedIn|Phone(?:\s*\/\s*WhatsApp)?|WhatsApp|GitHub|Website|Contact|Location))(?::\s*|\s*)(?!.*\*\*)(.+)$/gim,
        "$1:** $2"
      )
      // 5. Repair protocol omission in bare domain typo (e.g. "https.linkedin.com" -> "https://linkedin.com")
      .replace(/\bhttps?\.([a-zA-Z0-9-]+\.[a-zA-Z]{2,})/gi, "https://$1")
  );
}
