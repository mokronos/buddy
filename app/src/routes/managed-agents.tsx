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
  port: 8000
`;

type FeedbackState =
  | {
      kind: "error" | "success";
      message: string;
    }
  | null;

function FeedbackAlert(props: { feedback: FeedbackState; class?: string }) {
  if (!props.feedback) {
    return null;
  }

  const alertClass = props.feedback.kind === "error" ? "alert-error" : "alert-success";
  return <p class={`alert ${alertClass} text-sm ${props.class ?? ""}`}>{props.feedback.message}</p>;
}

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

  const [managedCreateFeedback, setManagedCreateFeedback] = createSignal<FeedbackState>(null);
  const [managedListFeedback, setManagedListFeedback] = createSignal<FeedbackState>(null);
  const [managedEditFeedback, setManagedEditFeedback] = createSignal<FeedbackState>(null);
  const [externalCreateFeedback, setExternalCreateFeedback] = createSignal<FeedbackState>(null);
  const [externalListFeedback, setExternalListFeedback] = createSignal<FeedbackState>(null);
  const [externalEditFeedback, setExternalEditFeedback] = createSignal<FeedbackState>(null);

  const [agentId, setAgentId] = createSignal("");
  const [image, setImage] = createSignal("buddy-agent-runtime:latest");
  const [containerPort, setContainerPort] = createSignal("8000");
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
  const managedQueryErrorMessage = () =>
    managedAgentsQuery.error instanceof Error ? managedAgentsQuery.error.message : null;
  const externalQueryErrorMessage = () =>
    externalAgentsQuery.error instanceof Error ? externalAgentsQuery.error.message : null;

  const clearManagedFeedback = (): void => {
    setManagedCreateFeedback(null);
    setManagedListFeedback(null);
    setManagedEditFeedback(null);
  };

  const clearExternalFeedback = (): void => {
    setExternalCreateFeedback(null);
    setExternalListFeedback(null);
    setExternalEditFeedback(null);
  };

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
    clearManagedFeedback();

    const trimmedAgentId = agentId().trim();
    if (trimmedAgentId.length === 0) {
      setManagedCreateFeedback({ kind: "error", message: "Agent id is required" });
      return;
    }

    const parsedContainerPort = Number.parseInt(containerPort(), 10);
    if (!Number.isFinite(parsedContainerPort) || parsedContainerPort <= 0) {
      setManagedCreateFeedback({
        kind: "error",
        message: "Container port must be a positive number",
      });
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
      setManagedCreateFeedback({
        kind: "success",
        message: `Created agent '${trimmedAgentId}'`,
      });
      await syncAgentQueries();
    } catch (error) {
      setManagedCreateFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to create agent",
      });
    }
  };

  const startAgent = async (managedAgentId: string): Promise<void> => {
    clearManagedFeedback();
    try {
      await startManagedMutation.mutateAsync(managedAgentId);
      setManagedListFeedback({
        kind: "success",
        message: `Started agent '${managedAgentId}'`,
      });
      await syncAgentQueries();
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to start agent",
      });
    }
  };

  const stopAgent = async (managedAgentId: string): Promise<void> => {
    clearManagedFeedback();
    try {
      await stopManagedMutation.mutateAsync(managedAgentId);
      setManagedListFeedback({
        kind: "success",
        message: `Stopped agent '${managedAgentId}'`,
      });
      await syncAgentQueries();
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to stop agent",
      });
    }
  };

  const removeAgent = async (managedAgentId: string): Promise<void> => {
    if (isDeletingManagedAgent(managedAgentId)) {
      return;
    }

    clearManagedFeedback();
    addDeletingManagedAgent(managedAgentId);
    try {
      await deleteManagedMutation.mutateAsync(managedAgentId);
      const removed = await waitForManagedAgentRemoval(managedAgentId);
      if (!removed) {
        throw new Error(`Timed out waiting for '${managedAgentId}' to be removed`);
      }

      await syncAgentQueries();
      setManagedListFeedback({
        kind: "success",
        message: `Deleted agent '${managedAgentId}'`,
      });
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to delete agent",
      });
    } finally {
      removeDeletingManagedAgent(managedAgentId);
    }
  };

  const beginEditManagedAgent = async (managedAgentId: string): Promise<void> => {
    clearManagedFeedback();
    try {
      const loadedConfig = await getManagedAgentConfig(managedAgentId);
      setEditingManagedAgentId(managedAgentId);
      setEditingManagedConfigYaml(loadedConfig);
      setRestartManagedAfterConfigSave(true);
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Failed to load managed agent config",
      });
    }
  };

  const cancelEditManagedAgent = (): void => {
    setEditingManagedAgentId(null);
    setEditingManagedConfigYaml("");
    setRestartManagedAfterConfigSave(true);
    setManagedEditFeedback(null);
  };

  const saveManagedAgentConfig = async (managedAgentId: string): Promise<void> => {
    setManagedListFeedback(null);
    setManagedEditFeedback(null);
    const nextConfig = editingManagedConfigYaml().trim();
    if (nextConfig.length === 0) {
      setManagedEditFeedback({ kind: "error", message: "Config YAML cannot be empty" });
      return;
    }

    try {
      await updateManagedConfigMutation.mutateAsync({
        agentId: managedAgentId,
        config_yaml: nextConfig,
        restart: restartManagedAfterConfigSave(),
      });
      setManagedListFeedback({
        kind: "success",
        message: `Updated config for managed agent '${managedAgentId}'`,
      });
      cancelEditManagedAgent();
      await syncAgentQueries();
    } catch (error) {
      setManagedEditFeedback({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Failed to update managed agent config",
      });
    }
  };

  const addExternalAgent = async (event: SubmitEvent): Promise<void> => {
    event.preventDefault();
    clearExternalFeedback();

    const trimmedAgentId = externalAgentId().trim();
    const trimmedAgentUrl = externalAgentUrl().trim();
    if (trimmedAgentId.length === 0) {
      setExternalCreateFeedback({ kind: "error", message: "External agent id is required" });
      return;
    }
    if (trimmedAgentUrl.length === 0) {
      setExternalCreateFeedback({ kind: "error", message: "External agent URL is required" });
      return;
    }

    try {
      await createExternalMutation.mutateAsync({
        agent_id: trimmedAgentId,
        base_url: trimmedAgentUrl,
        use_legacy_card_path: externalUseLegacyCardPath(),
      });
      setExternalCreateFeedback({
        kind: "success",
        message: `Added external agent '${trimmedAgentId}'`,
      });
      setExternalAgentId("");
      setExternalAgentUrl("");
      setExternalUseLegacyCardPath(false);
      await syncAgentQueries();
    } catch (error) {
      setExternalCreateFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to add external agent",
      });
    }
  };

  const removeExternalAgent = async (externalId: string): Promise<void> => {
    clearExternalFeedback();
    try {
      await deleteExternalMutation.mutateAsync(externalId);
      setExternalListFeedback({
        kind: "success",
        message: `Deleted external agent '${externalId}'`,
      });
      await syncAgentQueries();
    } catch (error) {
      setExternalListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to delete external agent",
      });
    }
  };

  const beginEditExternalAgent = (externalAgent: ExternalAgent): void => {
    clearExternalFeedback();
    setEditingExternalAgentId(externalAgent.agent_id);
    setEditingExternalAgentUrl(externalAgent.base_url);
    setEditingExternalUseLegacyCardPath(externalAgent.use_legacy_card_path);
  };

  const cancelEditExternalAgent = (): void => {
    setEditingExternalAgentId(null);
    setEditingExternalAgentUrl("");
    setEditingExternalUseLegacyCardPath(false);
    setExternalEditFeedback(null);
  };

  const saveExternalAgentEdit = async (agentId: string): Promise<void> => {
    setExternalListFeedback(null);
    setExternalEditFeedback(null);
    const trimmedUrl = editingExternalAgentUrl().trim();
    if (trimmedUrl.length === 0) {
      setExternalEditFeedback({ kind: "error", message: "External agent URL is required" });
      return;
    }
    try {
      await updateExternalMutation.mutateAsync({
        agentId,
        base_url: trimmedUrl,
        use_legacy_card_path: editingExternalUseLegacyCardPath(),
      });
      setExternalListFeedback({
        kind: "success",
        message: `Updated external agent '${agentId}'`,
      });
      cancelEditExternalAgent();
      await syncAgentQueries();
    } catch (error) {
      setExternalEditFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to update external agent",
      });
    }
  };

  return (
    <main class="flex min-h-screen flex-col">
      <TopTabs />
      <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4 lg:px-6">
        <div class="mx-auto flex w-full max-w-6xl flex-col gap-6">
          <div class="hero rounded-box border border-base-100/10 bg-base-100 shadow-xl">
            <div class="hero-content w-full justify-start p-6">
              <div>
                <div class="badge badge-primary badge-outline mb-3">Control Plane</div>
                <h1 class="text-3xl font-semibold">Managed Agents</h1>
                <p class="mt-2 text-sm text-base-content/70">
                  Create, start, stop and delete Docker-backed agent containers.
                </p>
              </div>
            </div>
          </div>

          <section class="card border border-base-100/10 bg-base-100 shadow-xl">
            <div class="card-body">
              <h2 class="card-title">Create Agent</h2>
            <form class="grid gap-3" onSubmit={createAgent}>
              <input
                class="input input-bordered w-full"
                placeholder="Agent ID (example: demo-agent)"
                value={agentId()}
                onInput={(event) => setAgentId(event.currentTarget.value)}
              />
              <input
                class="input input-bordered w-full"
                placeholder="Image"
                value={image()}
                onInput={(event) => setImage(event.currentTarget.value)}
              />
              <div class="grid gap-3 md:grid-cols-2">
                <input
                  class="input input-bordered w-full"
                  placeholder="Container Port"
                  value={containerPort()}
                  onInput={(event) => setContainerPort(event.currentTarget.value)}
                />
                <input
                  class="input input-bordered w-full"
                  placeholder="Config Mount Path"
                  value={configMountPath()}
                  onInput={(event) => setConfigMountPath(event.currentTarget.value)}
                />
              </div>
              <textarea
                class="textarea textarea-primary h-52 w-full font-mono text-xs"
                value={configYaml()}
                onInput={(event) => setConfigYaml(event.currentTarget.value)}
              />
              <button
                type="submit"
                disabled={createManagedMutation.isPending}
                class="btn btn-primary w-fit"
              >
                {createManagedMutation.isPending ? (
                  <>
                    <span class="loading loading-spinner loading-sm" />
                    Creating...
                  </>
                ) : (
                  "Create and Start"
                )}
              </button>
              <FeedbackAlert feedback={managedCreateFeedback()} />
              {createManagedMutation.isPending ? (
                <p class="alert alert-info text-sm">
                  <span class="loading loading-spinner loading-sm" />
                  Starting managed agent container and waiting for readiness...
                </p>
              ) : null}
            </form>
            </div>
          </section>

          <section class="card border border-base-100/10 bg-base-100 shadow-xl">
            <div class="card-body">
              <h2 class="card-title">Add External A2A Agent</h2>
            <p class="mb-4 text-sm text-base-content/70">
              Register an external Buddy-compatible server URL and access it through the local proxy.
            </p>
            <form class="grid gap-3" onSubmit={addExternalAgent}>
              <input
                class="input input-bordered w-full"
                placeholder="External Agent ID (example: remote-buddy)"
                value={externalAgentId()}
                onInput={(event) => setExternalAgentId(event.currentTarget.value)}
              />
              <input
                class="input input-bordered w-full"
                placeholder="Base URL (example: http://192.168.1.20:10001)"
                value={externalAgentUrl()}
                onInput={(event) => setExternalAgentUrl(event.currentTarget.value)}
              />
              <label class="label cursor-pointer justify-start gap-3">
                <input
                  type="checkbox"
                  class="checkbox checkbox-primary"
                  checked={externalUseLegacyCardPath()}
                  onChange={(event) => setExternalUseLegacyCardPath(event.currentTarget.checked)}
                />
                <span class="label-text">Use legacy card path (`/.well-known/agent.json`)</span>
              </label>
              <button
                type="submit"
                disabled={createExternalMutation.isPending}
                class="btn btn-secondary w-fit"
              >
                {createExternalMutation.isPending ? (
                  <>
                    <span class="loading loading-spinner loading-sm" />
                    Adding...
                  </>
                ) : (
                  "Add External Agent"
                )}
              </button>
              <FeedbackAlert feedback={externalCreateFeedback()} />
            </form>
            </div>
          </section>

          <section class="card border border-base-100/10 bg-base-100 shadow-xl">
            <div class="card-body">
            <div class="mb-4 flex items-center justify-between">
              <h2 class="card-title">Current Agents</h2>
              <button
                type="button"
                class="btn btn-sm btn-outline"
                onClick={() => {
                  void syncAgentQueries();
                }}
              >
                Refresh
              </button>
            </div>

            <FeedbackAlert
              feedback={
                managedListFeedback() ??
                (managedQueryErrorMessage()
                  ? { kind: "error", message: managedQueryErrorMessage() ?? "" }
                  : null)
              }
              class="mb-3"
            />

            <div class="grid gap-3">
              {shouldShowLoading() && visibleManagedAgents().length === 0 ? (
                <>
                  <article class="card border border-base-300 bg-base-200">
                    <div class="card-body p-4">
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
                    </div>
                  </article>
                  <article class="card border border-base-300 bg-base-200">
                    <div class="card-body p-4">
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
                    </div>
                  </article>
                </>
              ) : null}
              <For each={visibleManagedAgents()}>
                {(agent) => (
                  <article class="card border border-base-300 bg-base-200 shadow-sm">
                    <div class="card-body p-4">
                    {(() => {
                      const deleting = () => isDeletingManagedAgent(agent.agent_id);
                      return (
                        <>
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p class="font-medium">{agent.agent_id}</p>
                        <p class="text-xs text-base-content/60">{agent.image}</p>
                      </div>
                      <span class={`badge badge-outline ${deleting() ? "badge-warning" : "badge-neutral"}`}>
                        {deleting() ? "deleting" : agent.status}
                      </span>
                    </div>
                    <div class="mt-2 text-xs text-base-content/60">
                      <p>container: {agent.container_id ?? "-"}</p>
                      <p>host port: {agent.host_port ?? "-"}</p>
                      <p>config: {agent.config_path}</p>
                      {agent.last_error ? <p class="mt-1 text-error">error: {agent.last_error}</p> : null}
                      {deleting() ? (
                        <p class="mt-1 inline-flex items-center gap-2 text-warning">
                          <span class="loading loading-spinner loading-xs" />
                          Waiting for container shutdown...
                        </p>
                      ) : null}
                    </div>
                    <div class="join mt-3 flex flex-wrap">
                      <button
                        type="button"
                        disabled={deleting()}
                        class="btn btn-sm join-item"
                        onClick={() => void startAgent(agent.agent_id)}
                      >
                        Start
                      </button>
                      <button
                        type="button"
                        disabled={deleting()}
                        class="btn btn-sm join-item"
                        onClick={() => void stopAgent(agent.agent_id)}
                      >
                        Stop
                      </button>
                      <button
                        type="button"
                        disabled={deleting()}
                        class="btn btn-sm join-item"
                        onClick={() => void beginEditManagedAgent(agent.agent_id)}
                      >
                        Edit Config
                      </button>
                      <button
                        type="button"
                        disabled={deleting()}
                        class="btn btn-sm btn-error join-item"
                        onClick={() => void removeAgent(agent.agent_id)}
                      >
                        {deleting() ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                    {editingManagedAgentId() === agent.agent_id ? (
                      <div class="mt-3 grid gap-2">
                        <textarea
                          class="textarea textarea-primary h-48 w-full font-mono text-xs"
                          value={editingManagedConfigYaml()}
                          onInput={(event) => setEditingManagedConfigYaml(event.currentTarget.value)}
                        />
                        <FeedbackAlert feedback={managedEditFeedback()} />
                        <label class="label cursor-pointer justify-start gap-3">
                          <input
                            type="checkbox"
                            class="checkbox checkbox-primary checkbox-sm"
                            checked={restartManagedAfterConfigSave()}
                            onChange={(event) => setRestartManagedAfterConfigSave(event.currentTarget.checked)}
                          />
                          <span class="label-text text-xs">Restart container after save</span>
                        </label>
                        <div class="join flex flex-wrap">
                          <button
                            type="button"
                            disabled={updateManagedConfigMutation.isPending || deleting()}
                            class="btn btn-sm btn-primary join-item"
                            onClick={() => void saveManagedAgentConfig(agent.agent_id)}
                          >
                            Save Config
                          </button>
                          <button
                            type="button"
                            disabled={deleting()}
                            class="btn btn-sm join-item"
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
                    </div>
                  </article>
                )}
              </For>
              {visibleManagedAgents().length === 0 && !shouldShowLoading() ? (
                <p class="text-sm text-base-content/60">0 managed agents available.</p>
              ) : null}
            </div>
            </div>
          </section>

          <section class="card border border-base-100/10 bg-base-100 shadow-xl">
            <div class="card-body">
            <div class="mb-4 flex items-center justify-between">
              <h2 class="card-title">External Agents</h2>
            </div>
            <FeedbackAlert
              feedback={
                externalListFeedback() ??
                (externalQueryErrorMessage()
                  ? { kind: "error", message: externalQueryErrorMessage() ?? "" }
                  : null)
              }
              class="mb-3"
            />
            <div class="grid gap-3">
              {shouldShowLoading() && visibleExternalAgents().length === 0 ? (
                <>
                  <article class="card border border-base-300 bg-base-200">
                    <div class="card-body p-4">
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
                    </div>
                  </article>
                  <article class="card border border-base-300 bg-base-200">
                    <div class="card-body p-4">
                    <div class="flex items-center justify-between">
                      <div class="space-y-2">
                        <Skeleton class="h-4 w-32" />
                        <Skeleton class="h-3 w-52" />
                      </div>
                      <Skeleton class="h-6 w-20" />
                    </div>
                    </div>
                  </article>
                </>
              ) : null}
              <For each={visibleExternalAgents()}>
                {(externalAgent) => (
                  <article class="card border border-base-300 bg-base-200 shadow-sm">
                    <div class="card-body p-4">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p class="font-medium">{externalAgent.agent_id}</p>
                        <p class="text-xs text-base-content/60">{externalAgent.base_url}</p>
                      </div>
                      <span class="badge badge-neutral badge-outline">registered</span>
                    </div>
                    <div class="mt-2 text-xs text-base-content/60">
                      <p>proxy: /a2a/external/{externalAgent.agent_id}</p>
                      <p>card path: {externalAgent.use_legacy_card_path ? "legacy" : "standard"}</p>
                    </div>
                    {editingExternalAgentId() === externalAgent.agent_id ? (
                      <div class="mt-3 grid gap-2">
                        <input
                          class="input input-bordered w-full text-xs"
                          value={editingExternalAgentUrl()}
                          onInput={(event) => setEditingExternalAgentUrl(event.currentTarget.value)}
                        />
                        <FeedbackAlert feedback={externalEditFeedback()} />
                        <label class="label cursor-pointer justify-start gap-3">
                          <input
                            type="checkbox"
                            class="checkbox checkbox-primary checkbox-sm"
                            checked={editingExternalUseLegacyCardPath()}
                            onChange={(event) => setEditingExternalUseLegacyCardPath(event.currentTarget.checked)}
                          />
                          <span class="label-text text-xs">Use legacy card path (`/.well-known/agent.json`)</span>
                        </label>
                        <div class="join flex flex-wrap">
                          <button
                            type="button"
                            disabled={updateExternalMutation.isPending}
                            class="btn btn-sm btn-primary join-item"
                            onClick={() => void saveExternalAgentEdit(externalAgent.agent_id)}
                          >
                            Save
                          </button>
                          <button
                            type="button"
                            class="btn btn-sm join-item"
                            onClick={cancelEditExternalAgent}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div class="join mt-3 flex flex-wrap">
                        <button
                          type="button"
                          class="btn btn-sm join-item"
                          onClick={() => beginEditExternalAgent(externalAgent)}
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          class="btn btn-sm btn-error join-item"
                          onClick={() => void removeExternalAgent(externalAgent.agent_id)}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                    </div>
                  </article>
                )}
              </For>
              {visibleExternalAgents().length === 0 && !shouldShowLoading() ? (
                <p class="text-sm text-base-content/60">0 external agents available.</p>
              ) : null}
            </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
