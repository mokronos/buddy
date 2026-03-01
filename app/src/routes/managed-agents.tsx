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
  listManagedAgents,
  startManagedAgent,
  stopManagedAgent,
  type ManagedAgent,
} from "~/a2a/managedAgents";
import TopTabs from "~/components/TopTabs";

const defaultConfigYaml = `agent:
  id: demo-agent
  name: Demo Agent
  instructions: "You are a helpful assistant."
  model: openrouter:openrouter/free

a2a:
  port: 10001
`;

export default function ManagedAgentsPage() {
  const [agents, setAgents] = createSignal<ManagedAgent[]>([]);
  const [externalAgents, setExternalAgents] = createSignal<ExternalAgent[]>([]);
  const [loading, setLoading] = createSignal(true);
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);
  const [actionMessage, setActionMessage] = createSignal<string | null>(null);
  const [isCreating, setIsCreating] = createSignal(false);
  const [isAddingExternal, setIsAddingExternal] = createSignal(false);

  const [agentId, setAgentId] = createSignal("");
  const [image, setImage] = createSignal("buddy-agent-runtime:latest");
  const [containerPort, setContainerPort] = createSignal("10001");
  const [configMountPath, setConfigMountPath] = createSignal("/etc/buddy/agent.yaml");
  const [configYaml, setConfigYaml] = createSignal(defaultConfigYaml);
  const [externalAgentId, setExternalAgentId] = createSignal("");
  const [externalAgentUrl, setExternalAgentUrl] = createSignal("");
  const [externalUseLegacyCardPath, setExternalUseLegacyCardPath] = createSignal(false);
  const [editingExternalAgentId, setEditingExternalAgentId] = createSignal<string | null>(null);
  const [editingExternalAgentUrl, setEditingExternalAgentUrl] = createSignal("");
  const [editingExternalUseLegacyCardPath, setEditingExternalUseLegacyCardPath] = createSignal(false);
  const [isSavingExternalEdit, setIsSavingExternalEdit] = createSignal(false);

  const loadAgents = async (): Promise<void> => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [managed, external] = await Promise.all([listManagedAgents(), listExternalAgents()]);
      setAgents(managed);
      setExternalAgents(external);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to load managed agents");
    } finally {
      setLoading(false);
    }
  };

  onMount(async () => {
    await loadAgents();
  });

  const createAgent = async (event: SubmitEvent): Promise<void> => {
    event.preventDefault();
    setActionMessage(null);
    setErrorMessage(null);
    setIsCreating(true);

    const trimmedAgentId = agentId().trim();
    if (trimmedAgentId.length === 0) {
      setErrorMessage("Agent id is required");
      setIsCreating(false);
      return;
    }

    const parsedContainerPort = Number.parseInt(containerPort(), 10);
    if (!Number.isFinite(parsedContainerPort) || parsedContainerPort <= 0) {
      setErrorMessage("Container port must be a positive number");
      setIsCreating(false);
      return;
    }

    try {
      await createManagedAgent({
        agent_id: trimmedAgentId,
        image: image().trim(),
        config_yaml: configYaml(),
        container_port: parsedContainerPort,
        config_mount_path: configMountPath().trim(),
      });
      setActionMessage(`Created agent '${trimmedAgentId}'`);
      await loadAgents();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to create agent");
    } finally {
      setIsCreating(false);
    }
  };

  const startAgent = async (managedAgentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await startManagedAgent(managedAgentId);
      setActionMessage(`Started agent '${managedAgentId}'`);
      await loadAgents();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to start agent");
    }
  };

  const stopAgent = async (managedAgentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await stopManagedAgent(managedAgentId);
      setActionMessage(`Stopped agent '${managedAgentId}'`);
      await loadAgents();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to stop agent");
    }
  };

  const removeAgent = async (managedAgentId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await deleteManagedAgent(managedAgentId);
      setActionMessage(`Deleted agent '${managedAgentId}'`);
      await loadAgents();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to delete agent");
    }
  };

  const addExternalAgent = async (event: SubmitEvent): Promise<void> => {
    event.preventDefault();
    setActionMessage(null);
    setErrorMessage(null);
    setIsAddingExternal(true);

    const trimmedAgentId = externalAgentId().trim();
    const trimmedAgentUrl = externalAgentUrl().trim();
    if (trimmedAgentId.length === 0) {
      setErrorMessage("External agent id is required");
      setIsAddingExternal(false);
      return;
    }
    if (trimmedAgentUrl.length === 0) {
      setErrorMessage("External agent URL is required");
      setIsAddingExternal(false);
      return;
    }

    try {
      await createExternalAgent({
        agent_id: trimmedAgentId,
        base_url: trimmedAgentUrl,
        use_legacy_card_path: externalUseLegacyCardPath(),
      });
      setActionMessage(`Added external agent '${trimmedAgentId}'`);
      setExternalAgentId("");
      setExternalAgentUrl("");
      setExternalUseLegacyCardPath(false);
      await loadAgents();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to add external agent");
    } finally {
      setIsAddingExternal(false);
    }
  };

  const removeExternalAgent = async (externalId: string): Promise<void> => {
    setActionMessage(null);
    setErrorMessage(null);
    try {
      await deleteExternalAgent(externalId);
      setActionMessage(`Deleted external agent '${externalId}'`);
      await loadAgents();
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
    setIsSavingExternalEdit(true);
    const trimmedUrl = editingExternalAgentUrl().trim();
    if (trimmedUrl.length === 0) {
      setErrorMessage("External agent URL is required");
      setIsSavingExternalEdit(false);
      return;
    }
    try {
      await updateExternalAgent(agentId, {
        base_url: trimmedUrl,
        use_legacy_card_path: editingExternalUseLegacyCardPath(),
      });
      setActionMessage(`Updated external agent '${agentId}'`);
      cancelEditExternalAgent();
      await loadAgents();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to update external agent");
    } finally {
      setIsSavingExternalEdit(false);
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
                disabled={isCreating()}
                class="inline-flex w-fit items-center gap-2 rounded-md bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isCreating() ? (
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
                disabled={isAddingExternal()}
                class="inline-flex w-fit items-center gap-2 rounded-md bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isAddingExternal() ? (
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
                onClick={() => void loadAgents()}
              >
                Refresh
              </button>
            </div>

            {loading() ? <p class="text-zinc-400">Loading...</p> : null}
            {errorMessage() ? (
              <p class="mb-3 rounded-md bg-red-900/30 p-2 text-sm text-red-300">{errorMessage()}</p>
            ) : null}
            {actionMessage() ? (
              <p class="mb-3 rounded-md bg-emerald-900/30 p-2 text-sm text-emerald-300">{actionMessage()}</p>
            ) : null}
            {isCreating() ? (
              <p class="mb-3 inline-flex items-center gap-2 rounded-md bg-zinc-800 p-2 text-sm text-zinc-200">
                <span class="inline-block h-4 w-4 animate-spin rounded-full border-2 border-zinc-200 border-t-transparent" />
                Starting managed agent container and waiting for readiness...
              </p>
            ) : null}

            <div class="grid gap-3">
              <For each={agents()}>
                {(agent) => (
                  <article class="rounded-lg border border-zinc-800 bg-zinc-950 p-3">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p class="font-medium text-zinc-100">{agent.agent_id}</p>
                        <p class="text-xs text-zinc-400">{agent.image}</p>
                      </div>
                      <span class="rounded-md border border-zinc-700 px-2 py-1 text-xs uppercase tracking-wide text-zinc-300">
                        {agent.status}
                      </span>
                    </div>
                    <div class="mt-2 text-xs text-zinc-400">
                      <p>container: {agent.container_id ?? "-"}</p>
                      <p>host port: {agent.host_port ?? "-"}</p>
                      <p>config: {agent.config_path}</p>
                      {agent.last_error ? <p class="mt-1 text-red-300">error: {agent.last_error}</p> : null}
                    </div>
                    <div class="mt-3 flex flex-wrap gap-2">
                      <button
                        type="button"
                        class="rounded-md border border-zinc-700 px-3 py-1 text-xs hover:border-zinc-400"
                        onClick={() => void startAgent(agent.agent_id)}
                      >
                        Start
                      </button>
                      <button
                        type="button"
                        class="rounded-md border border-zinc-700 px-3 py-1 text-xs hover:border-zinc-400"
                        onClick={() => void stopAgent(agent.agent_id)}
                      >
                        Stop
                      </button>
                      <button
                        type="button"
                        class="rounded-md border border-red-700 px-3 py-1 text-xs text-red-300 hover:border-red-500"
                        onClick={() => void removeAgent(agent.agent_id)}
                      >
                        Delete
                      </button>
                    </div>
                  </article>
                )}
              </For>
              {agents().length === 0 && !loading() ? <p class="text-sm text-zinc-400">No managed agents yet.</p> : null}
            </div>
          </section>

          <section class="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
            <div class="mb-4 flex items-center justify-between">
              <h2 class="text-lg font-medium">External Agents</h2>
            </div>
            <div class="grid gap-3">
              <For each={externalAgents()}>
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
                            disabled={isSavingExternalEdit()}
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
              {externalAgents().length === 0 ? <p class="text-sm text-zinc-400">No external agents yet.</p> : null}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
