import type { AgentEndpoint } from "~/context/AgentsContext";

interface AgentCardProps {
  agent: AgentEndpoint;
  isActive: boolean;
  onSelect: (agentKey: string) => void;
}

export default function AgentCard(props: AgentCardProps) {
  const visibleSkills = props.agent.skills.slice(0, 3);

  return (
    <button
      type="button"
      class={`card w-full border text-left transition-all ${
        props.isActive
          ? "border-primary bg-primary/10 shadow-lg shadow-primary/10"
          : "border-base-300 bg-base-200/70 hover:border-primary/40 hover:bg-base-200"
      }`}
      aria-pressed={props.isActive}
      onClick={() => props.onSelect(props.agent.key)}
    >
      <div class="card-body gap-3 p-4">
        <div class="flex items-start justify-between gap-2">
          <div>
            <p class="card-title text-sm">{props.agent.name}</p>
            <p class="mt-1 text-[11px] uppercase tracking-[0.2em] text-base-content/50">{props.agent.key}</p>
          </div>
          {props.agent.version ? <span class="badge badge-primary badge-outline">v{props.agent.version}</span> : null}
        </div>

        <p class="text-xs leading-5 text-base-content/70">{props.agent.description ?? "No description provided."}</p>

        {visibleSkills.length > 0 ? (
          <div class="flex flex-wrap gap-1.5">
            {visibleSkills.map((skill) => (
              <span class="badge badge-secondary badge-outline badge-sm">{skill}</span>
            ))}
          </div>
        ) : null}
      </div>
    </button>
  );
}
