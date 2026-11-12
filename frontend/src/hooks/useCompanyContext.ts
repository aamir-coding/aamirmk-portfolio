import { useEffect, useState } from "react";
import { fetchCompanyContext, type CompanyContext } from "../lib/api";

export function useCompanyContext(slug: string | null) {
  const [company, setCompany] = useState<CompanyContext | null>(null);

  useEffect(() => {
    if (!slug || slug.length > 64) return;
    const controller = new AbortController();
    const deadline = window.setTimeout(() => controller.abort(), 90_000);
    void fetchCompanyContext(slug, controller.signal)
      .then(context => {
        if (!controller.signal.aborted) setCompany(context);
      })
      .catch(() => {
        // The default cover is already available.
      })
      .finally(() => window.clearTimeout(deadline));
    return () => {
      window.clearTimeout(deadline);
      controller.abort();
    };
  }, [slug]);

  return company?.slug === slug ? company : null;
}
