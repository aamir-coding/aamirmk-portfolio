import { useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";

export function SidePanel({ title, onClose, children, open = true }: { title: string; onClose: () => void; children: ReactNode; open?: boolean }) {
  const headingId = useId();
  // Defer network-backed tools until opened. Keep drafts and created links on dismissal.
  const [visited, setVisited] = useState(open);
  const ref = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  useLayoutEffect(() => {
    if (!open) return;
    const dialog = ref.current!;
    const trigger = document.activeElement;
    setVisited(true);
    dialog.showModal();
    return () => {
      dialog.close();
      if (trigger instanceof HTMLElement && trigger.isConnected) trigger.focus({ preventScroll: true });
    };
  }, [open]);
  useLayoutEffect(() => {
    if (!open) return;
    heading.current?.focus({ preventScroll: true });
    if (ref.current) ref.current.scrollTop = 0;
  }, [title, open]);
  return <dialog ref={ref} className="portfolio-panel" aria-labelledby={headingId}
    onCancel={event => { event.preventDefault(); onClose(); }}
    onClick={event => {
      if (event.target !== ref.current) return;
      const bounds = event.currentTarget.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose();
    }}>
    <button className="panel-close" aria-label="Close panel" onClick={onClose}>×</button>
    <h2 id={headingId} ref={heading} tabIndex={-1}>{title}</h2>
    {(open || visited) && children}
  </dialog>;
}
