import type { PropsWithChildren } from "react";
import { Braces, Github, LayoutDashboard } from "lucide-react";
import { Link, NavLink } from "react-router-dom";

import { cn } from "../lib/cn";

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link className="flex items-center gap-2 font-semibold tracking-tight text-white" to="/">
            <span className="grid size-8 place-items-center rounded-lg bg-accent text-slate-950"><Braces size={18} /></span>
            DevTrace
          </Link>
          <nav aria-label="Primary navigation" className="flex items-center gap-2">
            <NavLink
              className={({ isActive }) => cn("rounded-md px-3 py-2 text-sm", isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white")}
              to="/"
            >
              <span className="flex items-center gap-2"><LayoutDashboard size={16} />Dashboard</span>
            </NavLink>
            <a aria-label="DevTrace source repository" className="rounded-md p-2 text-slate-400 hover:text-white" href="https://github.com/tanveersingh0902/DevTrace">
              <Github size={18} />
            </a>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-6 py-10">{children}</main>
    </div>
  );
}
