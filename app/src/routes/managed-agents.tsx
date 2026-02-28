import { For, createSignal, onMount } from "solid-js";
import {
  createManagedAgent,
  deleteManagedAgent,
  listManagedAgents,
  startManagedAgent,
  stopManagedAgent,
  type ManagedAgent,
} from "~/a2a/managedAgents";

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
  const [loading, setLoading] = createSignal(true);
  const [errorMessage, setErrorMessage] = createSignal<string | null>(null);
  const [actionMessage, setActionMessage] = createSignal<string | null>(null);

  const [agentId, setAgentId] = createSignal("");
  const [image, setImage] = createSignal("buddy-agent-runtime:latest");
  const [containerPort, setContainerPort] = createSignal("10001");
  const [configMountPath, setConfigMountPath] = createSignal("/etc/buddy/agent.yaml");
  const [configYaml, setConfigYaml] = createSignal(defaultConfigYaml);

  const loadAgents = async (): Promise<void> => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const data = await listManagedAgents();
      setAgents(data);
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

  return (
    <main class="min-h-screen bg-zinc-950 px-6 py-6 text-zinc-100">
      <div class="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-semibold">Managed Agents</h1>
            <p class="mt-1 text-sm text-zinc-400">Create, start, stop and delete Docker-backed agent containers.</p>
          </div>
          <a href="/" class="rounded-md border border-zinc-600 px-3 py-2 text-sm hover:border-zinc-400">
            Back to Chat
          </a>
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
              class="w-fit rounded-md bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white"
            >
              Create and Start
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
          {errorMessage() ? <p class="mb-3 rounded-md bg-red-900/30 p-2 text-sm text-red-300">{errorMessage()}</p> : null}
          {actionMessage() ? (
            <p class="mb-3 rounded-md bg-emerald-900/30 p-2 text-sm text-emerald-300">{actionMessage()}</p>
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
      </div>
    </main>
  );
}
