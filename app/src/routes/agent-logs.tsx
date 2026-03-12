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
    <main class="flex min-h-screen flex-col">
      <TopTabs />
      <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4 lg:px-6">
        <div class="mx-auto flex w-full max-w-7xl flex-col gap-6">
          <div class="hero rounded-box border border-base-100/10 bg-base-100 shadow-xl">
            <div class="hero-content w-full justify-between p-6">
              <div>
                <div class="badge badge-accent badge-outline mb-3">Observability</div>
                <h1 class="text-3xl font-semibold">Agent Logs</h1>
                <p class="mt-2 text-sm text-base-content/70">Live Docker logs for each managed agent (auto-refresh every 2s).</p>
              </div>
              <button
                type="button"
                class="btn btn-outline"
                onClick={() => {
                  void logsQuery.refetch();
                }}
              >
                Refresh
              </button>
            </div>
          </div>

          {lastUpdated() ? <p class="text-xs text-base-content/50">Last updated: {lastUpdated()}</p> : null}

          <div class="grid gap-4">
            {isInitialLoading() && agentOrder().length === 0 ? (
              <>
                <section class="card border border-base-300 bg-base-200">
                  <div class="card-body p-4">
                  <div class="mb-2 flex items-center justify-between gap-3">
                    <div class="space-y-2">
                      <Skeleton class="h-4 w-32" />
                      <Skeleton class="h-3 w-48" />
                    </div>
                    <Skeleton class="h-6 w-20" />
                  </div>
                  <Skeleton class="h-44 w-full" />
                  </div>
                </section>
                <section class="card border border-base-300 bg-base-200">
                  <div class="card-body p-4">
                  <div class="mb-2 flex items-center justify-between gap-3">
                    <div class="space-y-2">
                      <Skeleton class="h-4 w-28" />
                      <Skeleton class="h-3 w-44" />
                    </div>
                    <Skeleton class="h-6 w-20" />
                  </div>
                  <Skeleton class="h-44 w-full" />
                  </div>
                </section>
              </>
            ) : null}
            <For each={agentOrder()}>
              {(agentId) => {
                const entry = () => entriesById()[agentId];
                return (
                  <section class="card border border-base-300 bg-base-100 shadow-sm">
                    <div class="card-body p-4">
                    <div class="mb-2 flex items-center justify-between gap-3">
                      <div>
                        <p class="font-medium">{entry()?.agent.agent_id ?? agentId}</p>
                        <p class="text-xs text-base-content/60">{entry()?.agent.image ?? "-"}</p>
                      </div>
                      <span class="badge badge-neutral badge-outline">
                        {entry()?.agent.status ?? "unknown"}
                      </span>
                    </div>

                    <pre
                      ref={(element) => {
                        logContainers.set(agentId, element);
                      }}
                      onScroll={() => updateFollowState(agentId)}
                      class="mockup-code max-h-80 overflow-y-auto whitespace-pre-wrap rounded-box border border-base-300 bg-base-200 p-3 font-mono text-xs"
                    >
                      {entry()?.logs && entry()!.logs.length > 0 ? entry()!.logs : "(no logs yet)"}
                    </pre>
                    </div>
                  </section>
                );
              }}
            </For>

            {agentOrder().length === 0 && !isInitialLoading() ? (
              <p class="text-sm text-base-content/60">0 agents available for logs.</p>
            ) : null}
          </div>
        </div>
      </div>
    </main>
  );
}
