import type { PropsWithChildren, ReactNode } from "react";

import { cn } from "../lib/cn";

type CardProps = PropsWithChildren<{ className?: string; title?: ReactNode; description?: ReactNode }>;

export function Card({ children, className, title, description }: CardProps) {
  return (
    <section className={cn("rounded-xl border border-slate-800 bg-slate-900/70 p-6 shadow-panel", className)}>
      {title ? <h2 className="text-base font-semibold text-white">{title}</h2> : null}
      {description ? <p className="mt-1 text-sm text-slate-400">{description}</p> : null}
      {children ? <div className={title || description ? "mt-5" : undefined}>{children}</div> : null}
    </section>
  );
}
