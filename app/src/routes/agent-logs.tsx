import { useQuery } from "@tanstack/solid-query";
import { For, createEffect, createMemo, createSignal, onMount } from "solid-js";

import { getManagedAgentLogs, listManagedAgents, type ManagedAgent } from "~/a2a/managedAgents";
import TopTabs from "~/components/TopTabs";
import Skeleton from "~/components/ui/Skeleton";

interface AgentLogEntry {
  agent: ManagedAgent;
  logs: string;
}

async function fetchManagedAgentLogs(): Promise<AgentLogEntry[]> {
  let agents: ManagedAgent[] = [];
  try {
    agents = await listManagedAgents();
  } catch {
    return [];
  }

  const payloads = await Promise.allSettled(agents.map((agent) => getManagedAgentLogs(agent.agent_id, 250)));

  return payloads.map((payload, index) => {
    const agent = agents[index];
    if (payload.status === "fulfilled") {
      return {
        agent: payload.value.agent,
        logs: payload.value.logs,
      };
    }

    const reason = payload.reason;
    const message = reason instanceof Error ? reason.message : "Failed to fetch logs";
    return {
      agent,
      logs: `(failed to load logs: ${message})`,
    };
  });
}

export default function AgentLogsPage() {
  const [isClientReady, setIsClientReady] = createSignal(false);
  const [lastSuccessfulEntries, setLastSuccessfulEntries] = createSignal<AgentLogEntry[]>([]);
  onMount(() => setIsClientReady(true));

  const logsQuery = useQuery(() => ({
    queryKey: ["agents", "managed", "logs"],
    queryFn: fetchManagedAgentLogs,
    refetchInterval: 2000,
    refetchOnWindowFocus: false,
    suspense: false,
    throwOnError: false,
  }));

  const logContainers = new Map<string, HTMLPreElement>();
  const shouldFollowLogs = new Map<string, boolean>();
  const scrollThreshold = 24;
  const entries = createMemo(() => {
    if (!isClientReady()) {
      return [];
    }
    return logsQuery.data ?? lastSuccessfulEntries();
  });
  const isInitialLoading = () => !isClientReady() || (logsQuery.isPending && entries().length === 0);
  const isRefreshing = () => isClientReady() && logsQuery.isFetching && entries().length > 0;

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

  createEffect(() => {
    if (logsQuery.data) {
      setLastSuccessfulEntries(logsQuery.data);
    }
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

          {lastUpdated() ? <p class="text-xs text-zinc-500">Last updated: {lastUpdated()}</p> : null}
          {isRefreshing() ? <p class="text-xs text-zinc-500">Refreshing logs...</p> : null}

          <div class="grid gap-4">
            {isInitialLoading() && agentOrder().length === 0 ? (
              <>
                <section class="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
                  <div class="mb-2 flex items-center justify-between gap-3">
                    <div class="space-y-2">
                      <Skeleton class="h-4 w-32" />
                      <Skeleton class="h-3 w-48" />
                    </div>
                    <Skeleton class="h-6 w-20" />
                  </div>
                  <Skeleton class="h-44 w-full" />
                </section>
                <section class="rounded-lg border border-zinc-800 bg-zinc-900 p-3">
                  <div class="mb-2 flex items-center justify-between gap-3">
                    <div class="space-y-2">
                      <Skeleton class="h-4 w-28" />
                      <Skeleton class="h-3 w-44" />
                    </div>
                    <Skeleton class="h-6 w-20" />
                  </div>
                  <Skeleton class="h-44 w-full" />
                </section>
              </>
            ) : null}
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

            {agentOrder().length === 0 && !isInitialLoading() ? (
              <p class="text-sm text-zinc-400">0 agents available for logs.</p>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}
