import { useChat } from "~/context/ChatContext";
import AgentCard from "~/components/AgentCard";

export default function Sidebar() {
  const { agents, activeAgentKey, activeAgentName, setActiveAgentKey } = useChat();

  return (
    <div class="flex h-full w-1/4 min-w-72 flex-col gap-4 border-r border-zinc-700 bg-zinc-900 p-4 text-zinc-200">
      <div>
        <p class="text-xs uppercase tracking-wide text-zinc-400">Connected Agent</p>
        <p class="mt-1 text-sm font-medium text-zinc-100">{activeAgentName()}</p>
      </div>

      <div class="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
        <p class="text-xs uppercase tracking-wide text-zinc-400">Available Agents</p>
        {agents().map((agent) => (
          <AgentCard
            agent={agent}
            isActive={agent.key === activeAgentKey()}
            onSelect={(agentKey) => setActiveAgentKey(agentKey)}
          />
        ))}
      </div>
    </div>
  );
}
