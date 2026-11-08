import type { ReactNode } from "react";
import { AlertCircle, Inbox, LoaderCircle } from "lucide-react";

import { Button } from "./Button";

type StateProps = { title: string; description: string; action?: ReactNode };

function StateFrame({ icon, title, description, action }: StateProps & { icon: ReactNode }) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/40 p-8 text-center">
      <div className="mb-4 text-cyan-300">{icon}</div>
      <h2 className="text-base font-semibold text-white">{title}</h2>
      <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function LoadingState({ title = "Loading" }: Pick<StateProps, "title">) {
  return <StateFrame icon={<LoaderCircle className="animate-spin" />} title={title} description="Please wait." />;
}

export function EmptyState({ title, description, action }: StateProps) {
  return <StateFrame icon={<Inbox />} title={title} description={description} action={action} />;
}

export function ErrorState({ title, description, onRetry }: StateProps & { onRetry?: () => void }) {
  return (
    <StateFrame
      icon={<AlertCircle />}
      title={title}
      description={description}
      action={onRetry ? <Button variant="secondary" onClick={onRetry}>Try again</Button> : undefined}
    />
  );
}
