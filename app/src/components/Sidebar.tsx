import { useChat } from "~/context/ChatContext";

export default function Sidebar() {
  const { agents, activeAgentKey, activeAgentName, setActiveAgentKey } = useChat();

  return (
    <div class="flex h-full w-1/6 flex-col gap-4 border-r border-zinc-700 bg-zinc-900 p-4 text-zinc-200">
      <div>
        <p class="text-xs uppercase tracking-wide text-zinc-400">Connected Agent</p>
        <p class="mt-1 text-sm font-medium text-zinc-100">{activeAgentName()}</p>
      </div>

      <label class="flex flex-col gap-1 text-xs uppercase tracking-wide text-zinc-400" for="agent-select">
        Agent
        <select
          id="agent-select"
          class="rounded border border-zinc-700 bg-zinc-800 px-2 py-2 text-sm text-zinc-100 outline-none focus:border-zinc-500"
          value={activeAgentKey()}
          onChange={(event) => setActiveAgentKey(event.currentTarget.value)}
        >
          {agents().map((agent) => (
            <option value={agent.key}>{agent.name}</option>
          ))}
        </select>
      </label>
    </div>
  );
}
