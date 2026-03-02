import { useMutation, useQuery } from "@tanstack/solid-query";
import { For, createSignal, onMount } from "solid-js";
import {
  createExternalAgent,
  deleteExternalAgent,
  listExternalAgents,
  updateExternalAgent,
  type ExternalAgent,
} from "~/a2a/externalAgents";
import {
  createManagedAgent,
  deleteManagedAgent,
  getManagedAgentConfig,
  listManagedAgents,
  startManagedAgent,
  stopManagedAgent,
  updateManagedAgentConfig,
  type ManagedAgent,
} from "~/a2a/managedAgents";
import TopTabs from "~/components/TopTabs";
import Skeleton from "~/components/ui/Skeleton";
import { useAgents } from "~/context/AgentsContext";

const defaultConfigYaml = `agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are a helpful assistant."
  model: openrouter:openrouter/free

a2a:
  port: 10001
`;

function syncAgentIdInConfig(configYaml: string, agentId: string): string {
  const lines = configYaml.split(/\r?\n/);
  let inAgentSection = false;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!inAgentSection) {
      if (trimmed === "agent:") {
        inAgentSection = true;
      }
      continue;
    }

    if (trimmed.length === 0) {
      continue;
    }

    if (!line.startsWith(" ") && !line.startsWith("\t")) {
      break;
    }

    const idMatch = line.match(/^(\s*)id:\s*.*$/);
    if (idMatch) {
      lines[index] = `${idMatch[1]}id: ${agentId}`;
      return lines.join("\n");
    }
  }

  return configYaml;
}

export default function ManagedAgentsPage() {
  const { refreshAgents } = useAgents();
  const managedAgentsQuery = useQuery(() => ({
    queryKey: ["agents", "managed"],
    queryFn: listManagedAgents,
    suspense: false,
    throwOnError: false,
  }));
  const externalAgentsQuery = useQuery(() => ({
    queryKey: ["agents", "external"],
    queryFn: listExternalAgents,
    suspense: false,
    throwOnError: false,
  }));

  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);
  const [actionMessage, setActionMessage] = createSignal<string | null>(null);

  const [agentId, setAgentId] = createSignal("");
  const [image, setImage] = createSignal("buddy-agent-runtime:latest");
  const [containerPort, setContainerPort] = createSignal("10001");
  const [configMountPath, setConfigMountPath] = createSignal("/etc/buddy/agent.yaml");
  const [configYaml, setConfigYaml] = createSignal(defaultConfigYaml);
  const [editingManagedAgentId, setEditingManagedAgentId] = createSignal<string | null>(null);
  const [editingManagedConfigYaml, setEditingManagedConfigYaml] = createSignal("");
  const [restartManagedAfterConfigSave, setRestartManagedAfterConfigSave] = createSignal(true);
  const [externalAgentId, setExternalAgentId] = createSignal("");
  const [externalAgentUrl, setExternalAgentUrl] = createSignal("");
  const [externalUseLegacyCardPath, setExternalUseLegacyCardPath] = createSignal(false);
  const [editingExternalAgentId, setEditingExternalAgentId] = createSignal<string | null>(null);
  const [editingExternalAgentUrl, setEditingExternalAgentUrl] = createSignal("");
  const [editingExternalUseLegacyCardPath, setEditingExternalUseLegacyCardPath] = createSignal(false);
  const [deletingManagedAgentIds, setDeletingManagedAgentIds] = createSignal<string[]>([]);
  const [isClientReady, setIsClientReady] = createSignal(false);
  onMount(() => setIsClientReady(true));

  const isDeletingManagedAgent = (managedAgentId: string): boolean =>
    deletingManagedAgentIds().some((id) => id === managedAgentId);

  const addDeletingManagedAgent = (managedAgentId: string): void => {
    setDeletingManagedAgentIds((current) =>
      current.some((id) => id === managedAgentId) ? current : [...current, managedAgentId],
    );
  };

  const removeDeletingManagedAgent = (managedAgentId: string): void => {
    setDeletingManagedAgentIds((current) => current.filter((id) => id !== managedAgentId));
  };

  const syncAgentQueries = async (): Promise<void> => {
    await Promise.all([managedAgentsQuery.refetch(), externalAgentsQuery.refetch()]);
    await refreshAgents();
  };

  const createManagedMutation = useMutation(() => ({ mutationFn: createManagedAgent }));
  const startManagedMutation = useMutation(() => ({ mutationFn: startManagedAgent }));
  const stopManagedMutation = useMutation(() => ({ mutationFn: stopManagedAgent }));
  const deleteManagedMutation = useMutation(() => ({ mutationFn: deleteManagedAgent }));
  const updateManagedConfigMutation = useMutation(() => ({
    mutationFn: (variables: { agentId: string; config_yaml: string; restart: boolean }) =>
      updateManagedAgentConfig(variables.agentId, {
        config_yaml: variables.config_yaml,
        restart: variables.restart,
      }),
  }));
  const createExternalMutation = useMutation(() => ({ mutationFn: createExternalAgent }));
  const deleteExternalMutation = useMutation(() => ({ mutationFn: deleteExternalAgent }));
  const updateExternalMutation = useMutation(() => ({
    mutationFn: (variables: { agentId: string; base_url: string; use_legacy_card_path: boolean }) =>
      updateExternalAgent(variables.agentId, {
        base_url: variables.base_url,
        use_legacy_card_path: variables.use_legacy_card_path,
      }),
  }));
  const isLoadingAgents = () => managedAgentsQuery.isPending || externalAgentsQuery.isPending;
  const shouldShowLoading = () => !isClientReady() || isLoadingAgents();
  const managedAgents = () => managedAgentsQuery.data ?? [];
  const externalAgents = () => externalAgentsQuery.data ?? [];
  const visibleManagedAgents = () => (isClientReady() ? managedAgents() : []);
  const visibleExternalAgents = () => (isClientReady() ? externalAgents() : []);
  const queryErrorMessage = () => null;

  const waitForManagedAgentRemoval = async (managedAgentId: string): Promise<boolean> => {
    const maxAttempts = 20;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const result = await managedAgentsQuery.refetch();
      const agents = result.data ?? [];
      if (!agents.some((agent) => agent.agent_id === managedAgentId)) {
        return true;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    return false;
  };

  const createAgent = async (event: SubmitEvent): Promise<void> => {
    event.preventDefault();
    setActionMessage(null);
    setErrorMessage(null);

    const trimmedAgentId = agentId().trim();
    if (trimmedAgentId.length === 0) {
      setErrorMessage("Agent id is required");
      return;
    }

    const parsedContainerPort = Number.parseInt(containerPort(), 10);
    if (!Number.isFinite(parsedContainerPort) || parsedContainerPort <= 0) {
      setErrorMessage("Container port must be a positive number");
      return;
    }

    const syncedConfigYaml = syncAgentIdInConfig(configYaml(), trimmedAgentId);
    if (syncedConfigYaml !== configYaml()) {
      setConfigYaml(syncedConfigYaml);
    }

    try {
      await createManagedMutation.mutateAsync({
        agent_id: trimmedAgentId,
        image: image().trim(),
        config_yaml: syncedConfigYaml,
        container_port: parsedContainerPort,
        config_mount_path: configMountPath().trim(),
      });
      setActionMessage(`Created agent '${trimmedAgentId}'`);
      await syncAgentQueries();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to create agent");
    }
  };

  const startAgent = async (managedAgentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await startManagedMutation.mutateAsync(managedAgentId);
      setActionMessage(`Started agent '${managedAgentId}'`);
      await syncAgentQueries();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to start agent");
    }
  };

  const stopAgent = async (managedAgentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await stopManagedMutation.mutateAsync(managedAgentId);
      setActionMessage(`Stopped agent '${managedAgentId}'`);
      await syncAgentQueries();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to stop agent");
    }
  };

  const removeAgent = async (managedAgentId: string): Promise<void> => {
    if (isDeletingManagedAgent(managedAgentId)) {
      return;
    }

    setActionMessage(null);
    setErrorMessage(null);
    addDeletingManagedAgent(managedAgentId);
    try {
      await deleteManagedMutation.mutateAsync(managedAgentId);
      const removed = await waitForManagedAgentRemoval(managedAgentId);
      if (!removed) {
        throw new Error(`Timed out waiting for '${managedAgentId}' to be removed`);
      }

      await syncAgentQueries();
      setActionMessage(`Deleted agent '${managedAgentId}'`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to delete agent");
    } finally {
      removeDeletingManagedAgent(managedAgentId);
    }
  };

  const beginEditManagedAgent = async (managedAgentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      const loadedConfig = await getManagedAgentConfig(managedAgentId);
      setEditingManagedAgentId(managedAgentId);
      setEditingManagedConfigYaml(loadedConfig);
      setRestartManagedAfterConfigSave(true);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to load managed agent config");
    }
  };

  const cancelEditManagedAgent = (): void => {
    setEditingManagedAgentId(null);
    setEditingManagedConfigYaml("");
    setRestartManagedAfterConfigSave(true);
  };

  const saveManagedAgentConfig = async (managedAgentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    const nextConfig = editingManagedConfigYaml().trim();
    if (nextConfig.length === 0) {
      setErrorMessage("Config YAML cannot be empty");
      return;
    }

    try {
      await updateManagedConfigMutation.mutateAsync({
        agentId: managedAgentId,
        config_yaml: nextConfig,
        restart: restartManagedAfterConfigSave(),
      });
      setActionMessage(`Updated config for managed agent '${managedAgentId}'`);
      cancelEditManagedAgent();
      await syncAgentQueries();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to update managed agent config");
    }
  };

  const addExternalAgent = async (event: SubmitEvent): Promise<void> => {
    event.preventDefault();
    setActionMessage(null);
    setErrorMessage(null);

    const trimmedAgentId = externalAgentId().trim();
    const trimmedAgentUrl = externalAgentUrl().trim();
    if (trimmedAgentId.length === 0) {
      setErrorMessage("External agent id is required");
      return;
    }
    if (trimmedAgentUrl.length === 0) {
      setErrorMessage("External agent URL is required");
      return;
    }

    try {
      await createExternalMutation.mutateAsync({
        agent_id: trimmedAgentId,
        base_url: trimmedAgentUrl,
        use_legacy_card_path: externalUseLegacyCardPath(),
      });
      setActionMessage(`Added external agent '${trimmedAgentId}'`);
      setExternalAgentId("");
      setExternalAgentUrl("");
      setExternalUseLegacyCardPath(false);
      await syncAgentQueries();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to add external agent");
    }
  };

  const removeExternalAgent = async (externalId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await deleteExternalMutation.mutateAsync(externalId);
      setActionMessage(`Deleted external agent '${externalId}'`);
      await syncAgentQueries();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to delete external agent");
    }
  };

  const beginEditExternalAgent = (externalAgent: ExternalAgent): void => {
    setEditingExternalAgentId(externalAgent.agent_id);
    setEditingExternalAgentUrl(externalAgent.base_url);
    setEditingExternalUseLegacyCardPath(externalAgent.use_legacy_card_path);
  };

  const cancelEditExternalAgent = (): void => {
    setEditingExternalAgentId(null);
    setEditingExternalAgentUrl("");
    setEditingExternalUseLegacyCardPath(false);
  };

  const saveExternalAgentEdit = async (agentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    const trimmedUrl = editingExternalAgentUrl().trim();
    if (trimmedUrl.length === 0) {
      setErrorMessage("External agent URL is required");
      return;
    }
    try {
      await updateExternalMutation.mutateAsync({
        agentId,
        base_url: trimmedUrl,
        use_legacy_card_path: editingExternalUseLegacyCardPath(),
      });
      setActionMessage(`Updated external agent '${agentId}'`);
      cancelEditExternalAgent();
      await syncAgentQueries();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to update external agent");
    }
  };

  return (
    <main class="flex h-screen flex-col bg-zinc-950 text-zinc-100">
      <TopTabs />
      <div class="min-h-0 flex-1 overflow-y-auto px-6 py-6">
        <div class="mx-auto flex w-full max-w-6xl flex-col gap-6">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-semibold">Managed Agents</h1>
              <p class="mt-1 text-sm text-zinc-400">Create, start, stop and delete Docker-backed agent containers.</p>
            </div>
          </div>

          <section class="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <h2 class="mb-4 text-lg font-medium">Create Agent</h2>
            <form class="grid gap-3" onSubmit={createAgent}>
              <input
                class="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2"
                placeholder="Agent ID (example: demo-agent)"
                value={agentId()}
                onInput={(event) => setAgentId(event.currentTarget.value)}
              />
              <input
                class="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2"
                placeholder="Image"
                value={image()}
                onInput={(event) => setImage(event.currentTarget.value)}
              />
              <div class="grid gap-3 md:grid-cols-2">
                <input
                  class="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2"
                  placeholder="Container Port"
                  value={containerPort()}
                  onInput={(event) => setContainerPort(event.currentTarget.value)}
                />
                <input
                  class="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2"
                  placeholder="Config Mount Path"
                  value={configMountPath()}
                  onInput={(event) => setConfigMountPath(event.currentTarget.value)}
                />
              </div>
              <textarea
                class="h-52 rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 font-mono text-xs"
                value={configYaml()}
                onInput={(event) => setConfigYaml(event.currentTarget.value)}
              />
              <button
                type="submit"
                disabled={createManagedMutation.isPending}
                class="inline-flex w-fit items-center gap-2 rounded-md bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              >
                {createManagedMutation.isPending ? (
                  <>
                    <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-zinc-900 border-t-transparent" />
                    Creating...
                  </>
                ) : (
                  "Create and Start"
                )}
              </button>
            </form>
          </section>

          <section class="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <h2 class="mb-2 text-lg font-medium">Add External A2A Agent</h2>
            <p class="mb-4 text-sm text-zinc-400">
              Register an external Buddy-compatible server URL and access it through the local proxy.
            </p>
            <form class="grid gap-3" onSubmit={addExternalAgent}>
              <input
                class="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2"
                placeholder="External Agent ID (example: remote-buddy)"
                value={externalAgentId()}
                onInput={(event) => setExternalAgentId(event.currentTarget.value)}
              />
              <input
                class="rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2"
                placeholder="Base URL (example: http://192.168.1.20:10001)"
                value={externalAgentUrl()}
                onInput={(event) => setExternalAgentUrl(event.currentTarget.value)}
              />
              <label class="inline-flex items-center gap-2 text-sm text-zinc-300">
                <input
                  type="checkbox"
                  checked={externalUseLegacyCardPath()}
                  onChange={(event) => setExternalUseLegacyCardPath(event.currentTarget.checked)}
                />
                Use legacy card path (`/.well-known/agent.json`)
              </label>
              <button
                type="submit"
                disabled={createExternalMutation.isPending}
                class="inline-flex w-fit items-center gap-2 rounded-md bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              >
                {createExternalMutation.isPending ? (
                  <>
                    <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-zinc-900 border-t-transparent" />
                    Adding...
                  </>
                ) : (
                  "Add External Agent"
                )}
              </button>
            </form>
          </section>

          <section class="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <div class="mb-4 flex items-center justify-between">
              <h2 class="text-lg font-medium">Current Agents</h2>
              <button
                type="button"
                class="rounded-md border border-zinc-700 px-3 py-1 text-sm hover:border-zinc-400"
                onClick={() => {
                  void syncAgentQueries();
                }}
              >
                Refresh
              </button>
            </div>

            {errorMessage() || queryErrorMessage() ? (
              <p class="mb-3 rounded-md bg-red-900/30 p-2 text-sm text-red-300">{errorMessage() ?? queryErrorMessage()}</p>
            ) : null}
            {actionMessage() ? (
              <p class="mb-3 rounded-md bg-emerald-900/30 p-2 text-sm text-emerald-300">{actionMessage()}</p>
            ) : null}
            {createManagedMutation.isPending ? (
              <p class="mb-3 inline-flex items-center gap-2 rounded-md bg-zinc-800 p-2 text-sm text-zinc-200">
                <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-zinc-200 border-t-transparent" />
                Starting managed agent container and waiting for readiness...
              </p>
            ) : null}

            <div class="grid gap-3">
              {shouldShowLoading() && visibleManagedAgents().length === 0 ? (
                <>
                  <article class="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div class="flex items-center justify-between">
                      <div class="space-y-2">
                        <Skeleton class="h-4 w-32" />
                        <Skeleton class="h-3 w-48" />
                      </div>
                      <Skeleton class="h-6 w-20" />
                    </div>
                    <div class="mt-3 space-y-2">
                      <Skeleton class="h-3 w-full" />
                      <Skeleton class="h-3 w-2/3" />
                    </div>
                    <div class="mt-3 flex gap-2">
                      <Skeleton class="h-7 w-16" />
                      <Skeleton class="h-7 w-16" />
                      <Skeleton class="h-7 w-24" />
                    </div>
                  </article>
                  <article class="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div class="flex items-center justify-between">
                      <div class="space-y-2">
                        <Skeleton class="h-4 w-28" />
                        <Skeleton class="h-3 w-44" />
                      </div>
                      <Skeleton class="h-6 w-20" />
                    </div>
                    <div class="mt-3 space-y-2">
                      <Skeleton class="h-3 w-full" />
                      <Skeleton class="h-3 w-3/4" />
                    </div>
                  </article>
                </>
              ) : null}
              <For each={visibleManagedAgents()}>
                {(agent) => (
                  <article class="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    {(() => {
                      const deleting = () => isDeletingManagedAgent(agent.agent_id);
                      return (
                        <>
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p class="font-medium text-zinc-100">{agent.agent_id}</p>
                        <p class="text-xs text-zinc-400">{agent.image}</p>
                      </div>
                      <span class="rounded-md border border-zinc-700 px-2 py-1 text-xs uppercase tracking-wide text-zinc-300">
                        {deleting() ? "deleting" : agent.status}
                      </span>
                    </div>
                    <div class="mt-2 text-xs text-zinc-400">
                      <p>container: {agent.container_id ?? "-"}</p>
                      <p>host port: {agent.host_port ?? "-"}</p>
                      <p>config: {agent.config_path}</p>
                      {agent.last_error ? <p class="mt-1 text-red-300">error: {agent.last_error}</p> : null}
                      {deleting() ? (
                        <p class="mt-1 inline-flex items-center gap-2 text-amber-300">
                          <span class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-amber-300 border-t-transparent" />
                          Waiting for container shutdown...
                        </p>
                      ) : null}
                    </div>
                    <div class="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={deleting()}
                        class="rounded-md border border-zinc-700 px-3 py-1 text-xs hover:border-zinc-400 disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => void startAgent(agent.agent_id)}
                      >
                        Start
                      </button>
                      <button
                        type="button"
                        disabled={deleting()}
                        class="rounded-md border border-zinc-700 px-3 py-1 text-xs hover:border-zinc-400 disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => void stopAgent(agent.agent_id)}
                      >
                        Stop
                      </button>
                      <button
                        type="button"
                        disabled={deleting()}
                        class="rounded-md border border-zinc-700 px-3 py-1 text-xs hover:border-zinc-400 disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => void beginEditManagedAgent(agent.agent_id)}
                      >
                        Edit Config
                      </button>
                      <button
                        type="button"
                        disabled={deleting()}
                        class="rounded-md border border-red-700 px-3 py-1 text-xs text-red-300 hover:border-red-500 disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => void removeAgent(agent.agent_id)}
                      >
                        {deleting() ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                    {editingManagedAgentId() === agent.agent_id ? (
                      <div class="mt-3 grid gap-2">
                        <textarea
                          class="h-48 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs"
                          value={editingManagedConfigYaml()}
                          onInput={(event) => setEditingManagedConfigYaml(event.currentTarget.value)}
                        />
                        <label class="inline-flex items-center gap-2 text-xs text-zinc-300">
                          <input
                            type="checkbox"
                            checked={restartManagedAfterConfigSave()}
                            onChange={(event) => setRestartManagedAfterConfigSave(event.currentTarget.checked)}
                          />
                          Restart container after save
                        </label>
                        <div class="flex flex-wrap gap-2">
                          <button
                            type="button"
                            disabled={updateManagedConfigMutation.isPending || deleting()}
                            class="rounded-md border border-zinc-600 px-3 py-1 text-xs text-zinc-100 hover:border-zinc-400 disabled:cursor-not-allowed disabled:opacity-70"
                            onClick={() => void saveManagedAgentConfig(agent.agent_id)}
                          >
                            Save Config
                          </button>
                          <button
                            type="button"
                            disabled={deleting()}
                            class="rounded-md border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:border-zinc-500"
                            onClick={cancelEditManagedAgent}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : null}
                        </>
                      );
                    })()}
                  </article>
                )}
              </For>
              {visibleManagedAgents().length === 0 && !shouldShowLoading() ? (
                <p class="text-sm text-zinc-400">0 managed agents available.</p>
              ) : null}
            </div>
          </section>

          <section class="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <div class="mb-4 flex items-center justify-between">
              <h2 class="text-lg font-medium">External Agents</h2>
            </div>
            <div class="grid gap-3">
              {shouldShowLoading() && visibleExternalAgents().length === 0 ? (
                <>
                  <article class="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div class="flex items-center justify-between">
                      <div class="space-y-2">
                        <Skeleton class="h-4 w-36" />
                        <Skeleton class="h-3 w-56" />
                      </div>
                      <Skeleton class="h-6 w-20" />
                    </div>
                    <div class="mt-3 flex gap-2">
                      <Skeleton class="h-7 w-14" />
                      <Skeleton class="h-7 w-16" />
                    </div>
                  </article>
                  <article class="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div class="flex items-center justify-between">
                      <div class="space-y-2">
                        <Skeleton class="h-4 w-32" />
                        <Skeleton class="h-3 w-52" />
                      </div>
                      <Skeleton class="h-6 w-20" />
                    </div>
                  </article>
                </>
              ) : null}
              <For each={visibleExternalAgents()}>
                {(externalAgent) => (
                  <article class="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p class="font-medium text-zinc-100">{externalAgent.agent_id}</p>
                        <p class="text-xs text-zinc-400">{externalAgent.base_url}</p>
                      </div>
                      <span class="rounded-md border border-zinc-700 px-2 py-1 text-xs uppercase tracking-wide text-zinc-300">
                        registered
                      </span>
                    </div>
                    <div class="mt-2 text-xs text-zinc-400">
                      <p>proxy: /a2a/external/{externalAgent.agent_id}</p>
                      <p>card path: {externalAgent.use_legacy_card_path ? "legacy" : "standard"}</p>
                    </div>
                    {editingExternalAgentId() === externalAgent.agent_id ? (
                      <div class="mt-3 grid gap-2">
                        <input
                          class="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs"
                          value={editingExternalAgentUrl()}
                          onInput={(event) => setEditingExternalAgentUrl(event.currentTarget.value)}
                        />
                        <label class="inline-flex items-center gap-2 text-xs text-zinc-300">
                          <input
                            type="checkbox"
                            checked={editingExternalUseLegacyCardPath()}
                            onChange={(event) => setEditingExternalUseLegacyCardPath(event.currentTarget.checked)}
                          />
                          Use legacy card path (`/.well-known/agent.json`)
                        </label>
                        <div class="flex flex-wrap gap-2">
                          <button
                            type="button"
                            disabled={updateExternalMutation.isPending}
                            class="rounded-md border border-zinc-600 px-3 py-1 text-xs text-zinc-100 hover:border-zinc-400 disabled:cursor-not-allowed disabled:opacity-70"
                            onClick={() => void saveExternalAgentEdit(externalAgent.agent_id)}
                          >
                            Save
                          </button>
                          <button
                            type="button"
                            class="rounded-md border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:border-zinc-500"
                            onClick={cancelEditExternalAgent}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div class="mt-3 flex flex-wrap gap-2">
                        <button
                          type="button"
                          class="rounded-md border border-zinc-700 px-3 py-1 text-xs text-zinc-200 hover:border-zinc-500"
                          onClick={() => beginEditExternalAgent(externalAgent)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          class="rounded-md border border-red-700 px-3 py-1 text-xs text-red-300 hover:border-red-500"
                          onClick={() => void removeExternalAgent(externalAgent.agent_id)}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </article>
                )}
              </For>
              {visibleExternalAgents().length === 0 && !shouldShowLoading() ? (
                <p class="text-sm text-zinc-400">0 external agents available.</p>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
