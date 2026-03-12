import { useAgents } from "~/context/AgentsContext";
import AgentCard from "~/components/AgentCard";

export default function Sidebar() {
  const { agents, activeAgentKey, activeAgentName, setActiveAgentKey } = useAgents();

  return (
    <aside class="card h-full w-full border border-base-100/10 bg-base-100 shadow-xl lg:w-80">
      <div class="card-body min-h-0 gap-4">
        <div class="rounded-box border border-primary/20 bg-primary/10 p-4">
          <p class="text-xs uppercase tracking-[0.25em] text-primary/80">Connected Agent</p>
          <p class="mt-2 text-lg font-semibold text-base-content">{activeAgentName()}</p>
        </div>

        <div class="min-h-0 flex-1">
          <div class="mb-3 flex items-center justify-between">
            <p class="text-xs uppercase tracking-[0.25em] text-base-content/60">Available Agents</p>
            <span class="badge badge-outline">{agents().length}</span>
          </div>
          <div class="flex min-h-0 flex-col gap-3 overflow-y-auto pr-1">
            {agents().map((agent) => (
              <AgentCard
                agent={agent}
                isActive={agent.key === activeAgentKey()}
                onSelect={(agentKey) => setActiveAgentKey(agentKey)}
              />
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
