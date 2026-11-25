import { useLayoutEffect, useRef, type ReactNode } from "react";

export function SidePanel({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  useLayoutEffect(() => {
    const dialog = ref.current!;
    const trigger = document.activeElement;
    dialog.showModal();
    return () => {
      dialog.close();
      if (trigger instanceof HTMLElement && trigger.isConnected) trigger.focus({ preventScroll: true });
    };
  }, []);
  useLayoutEffect(() => {
    heading.current?.focus({ preventScroll: true });
    if (ref.current) ref.current.scrollTop = 0;
  }, [title]);
  return <dialog ref={ref} className="portfolio-panel" aria-labelledby="panel-heading"
    onCancel={event => { event.preventDefault(); onClose(); }}
    onClick={event => {
      if (event.target !== ref.current) return;
      const bounds = event.currentTarget.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose();
    }}>
    <button className="panel-close" aria-label="Close panel" onClick={onClose}>×</button>
    <h2 id="panel-heading" ref={heading} tabIndex={-1}>{title}</h2>
    {children}
  </dialog>;
}
