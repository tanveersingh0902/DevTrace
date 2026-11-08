import { ArrowRight, Layers3, Network, Sparkles } from "lucide-react";

import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/PageState";

const futureCapabilities = [
  { icon: Layers3, title: "Repository analysis", description: "Structural analysis will arrive in a later phase." },
  { icon: Network, title: "Architecture exploration", description: "Interactive dependency views are intentionally deferred." },
  { icon: Sparkles, title: "Grounded explanations", description: "AI capabilities will cite completed analysis snapshots." }
];

export function DashboardPage() {
  return (
    <div className="space-y-8">
      <section className="max-w-3xl">
        <p className="text-sm font-medium text-cyan-300">Codebase intelligence, built deliberately</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white sm:text-5xl">Understand the shape of unfamiliar software.</h1>
        <p className="mt-4 text-lg leading-8 text-slate-400">DevTrace is ready for local development. Project management and analysis will be added in subsequent phases.</p>
      </section>

      <EmptyState
        title="No projects yet"
        description="Project creation is introduced with the authentication and access-control phase."
        action={<Button disabled>New project <ArrowRight className="ml-2" size={16} /></Button>}
      />

      <div className="grid gap-4 md:grid-cols-3">
        {futureCapabilities.map(({ icon: Icon, title, description }) => (
          <Card key={title} title={title} description={description}>
            <Icon className="text-cyan-300" size={22} aria-hidden="true" />
          </Card>
        ))}
      </div>
    </div>
  );
}
