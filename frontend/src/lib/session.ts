const key = "amk_abuse_session_v1";
const validId = /^[A-Za-z0-9_-]{1,64}$/;
let fallbackId: string | undefined;

/** Opaque tab identity for abuse limits, never authentication or recruiter data. */
export function getSessionId(): string {
  try {
    const saved = sessionStorage.getItem(key);
    if (saved && validId.test(saved)) return saved;
  } catch { /* Storage may be blocked; keep a stable in-memory tab identity. */ }
  fallbackId ??= crypto.randomUUID();
  try { sessionStorage.setItem(key, fallbackId); } catch { /* Same fallback. */ }
  return fallbackId;
}
