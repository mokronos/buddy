import type { AgentEndpoint } from "~/context/ChatContext";

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
      class={`w-full rounded-lg border px-3 py-3 text-left transition ${
        props.isActive
          ? "border-cyan-500 bg-cyan-950/40 text-zinc-50"
          : "border-zinc-700 bg-zinc-800/70 text-zinc-200 hover:border-zinc-500 hover:bg-zinc-800"
      }`}
      aria-pressed={props.isActive}
      onClick={() => props.onSelect(props.agent.key)}
    >
      <div class="flex items-start justify-between gap-2">
        <p class="text-sm font-semibold text-zinc-50">{props.agent.name}</p>
        {props.agent.version ? (
          <span class="rounded bg-zinc-700/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-zinc-300">
            v{props.agent.version}
          </span>
        ) : null}
      </div>

      <p class="mt-2 text-xs text-zinc-300">{props.agent.description ?? "No description provided."}</p>

      {visibleSkills.length > 0 ? (
        <div class="mt-2 flex flex-wrap gap-1">
          {visibleSkills.map((skill) => (
            <span class="rounded bg-zinc-700/70 px-2 py-0.5 text-[10px] text-zinc-200">{skill}</span>
          ))}
        </div>
      ) : null}

      <p class="mt-2 text-[10px] uppercase tracking-wide text-zinc-400">{props.agent.key}</p>
    </button>
  );
}
