import { useQuery } from "@tanstack/solid-query";
import { For, createEffect, createMemo } from "solid-js";

import { getManagedAgentLogs, listManagedAgents, type ManagedAgent } from "~/a2a/managedAgents";
import TopTabs from "~/components/TopTabs";

interface AgentLogEntry {
  agent: ManagedAgent;
  logs: string;
}

async function fetchManagedAgentLogs(): Promise<AgentLogEntry[]> {
  const agents = await listManagedAgents();
  return Promise.all(
    agents.map(async (agent) => {
      const payload = await getManagedAgentLogs(agent.agent_id, 250);
      return {
        agent: payload.agent,
        logs: payload.logs,
      };
    }),
  );
}

export default function AgentLogsPage() {
  const logsQuery = useQuery(() => ({
    queryKey: ["agents", "managed", "logs"],
    queryFn: fetchManagedAgentLogs,
    refetchInterval: 2000,
    refetchOnWindowFocus: false,
  }));

  const logContainers = new Map<string, HTMLPreElement>();
  const shouldFollowLogs = new Map<string, boolean>();
  const scrollThreshold = 24;

  const entries = createMemo(() => logsQuery.data ?? []);
  const agentOrder = createMemo(() => entries().map((entry) => entry.agent.agent_id));
  const entriesById = createMemo(() => {
    const next: Record<string, AgentLogEntry> = {};
    for (const entry of entries()) {
      next[entry.agent.agent_id] = entry;
    }
    return next;
  });

  const scrollToBottom = (agentId: string): void => {
    const container = logContainers.get(agentId);
    if (!container) {
      return;
    }
    container.scrollTop = container.scrollHeight;
  };

  const updateFollowState = (agentId: string): void => {
    const container = logContainers.get(agentId);
    if (!container) {
      return;
    }

    const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    shouldFollowLogs.set(agentId, distanceFromBottom <= scrollThreshold);
  };

  const syncScrollingAfterRefresh = (agentIds: string[]): void => {
    queueMicrotask(() => {
      for (const agentId of agentIds) {
        if (!shouldFollowLogs.has(agentId)) {
          shouldFollowLogs.set(agentId, true);
        }

        if (shouldFollowLogs.get(agentId)) {
          scrollToBottom(agentId);
        }
      }
    });
  };

  createEffect(() => {
    syncScrollingAfterRefresh(agentOrder());
  });

  const lastUpdated = createMemo(() => {
    if (!logsQuery.dataUpdatedAt) {
      return "";
    }
    return new Date(logsQuery.dataUpdatedAt).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  });

  return (
    <main class="flex h-screen flex-col bg-zinc-950 text-zinc-100">
      <TopTabs />
      <div class="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        <div class="mx-auto flex w-full max-w-7xl flex-col gap-6">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-semibold">Agent Logs</h1>
              <p class="mt-1 text-sm text-zinc-400">Live Docker logs for each managed agent (auto-refresh every 2s).</p>
            </div>
            <button
              type="button"
              class="rounded-md border border-zinc-700 px-3 py-1 text-sm hover:border-zinc-400"
              onClick={() => {
                void logsQuery.refetch();
              }}
            >
              Refresh
            </button>
          </div>

          {logsQuery.isPending ? <p class="text-zinc-400">Loading logs...</p> : null}
          {logsQuery.isError ? (
            <p class="rounded-md bg-red-900/30 p-2 text-sm text-red-300">
              {logsQuery.error instanceof Error ? logsQuery.error.message : "Failed to load agent logs"}
            </p>
          ) : null}
          {lastUpdated() ? <p class="text-xs text-zinc-500">Last updated: {lastUpdated()}</p> : null}

          <div class="grid gap-4">
            <For each={agentOrder()}>
              {(agentId) => {
                const entry = () => entriesById()[agentId];
                return (
                  <section class="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
                    <div class="mb-2 flex items-center justify-between gap-3">
                      <div>
                        <p class="font-medium">{entry()?.agent.agent_id ?? agentId}</p>
                        <p class="text-xs text-zinc-400">{entry()?.agent.image ?? "-"}</p>
                      </div>
                      <span class="rounded-md border border-zinc-700 px-2 py-1 text-xs uppercase tracking-wide text-zinc-300">
                        {entry()?.agent.status ?? "unknown"}
                      </span>
                    </div>

                    <pre
                      ref={(element) => {
                        logContainers.set(agentId, element);
                      }}
                      onScroll={() => updateFollowState(agentId)}
                      class="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-md border border-zinc-800 bg-zinc-950 p-3 font-mono text-xs text-zinc-200"
                    >
                      {entry()?.logs && entry()!.logs.length > 0 ? entry()!.logs : "(no logs yet)"}
                    </pre>
                  </section>
                );
              }}
            </For>

            {agentOrder().length === 0 && !logsQuery.isPending ? (
              <p class="text-sm text-zinc-400">No managed agents found.</p>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}
