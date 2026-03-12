import { For, Show } from "solid-js";
import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";

export default function ManagedConfigFields(props: {
  config: RuntimeAgentConfigPayload;
  onChange: (config: RuntimeAgentConfigPayload) => void;
}) {
  const updateConfig = (nextConfig: RuntimeAgentConfigPayload): void => {
    props.onChange(nextConfig);
  };

  const updateMcpServer = (index: number, url: string): void => {
    updateConfig({
      ...props.config,
      mcp_servers: props.config.mcp_servers.map((server, serverIndex) =>
        serverIndex === index ? { ...server, url } : server,
      ),
    });
  };

  const addMcpServer = (): void => {
    updateConfig({
      ...props.config,
      mcp_servers: [...props.config.mcp_servers, { url: "" }],
    });
  };

  const removeMcpServer = (index: number): void => {
    updateConfig({
      ...props.config,
      mcp_servers: props.config.mcp_servers.filter((_, serverIndex) => serverIndex !== index),
    });
  };

  return (
    <div class="grid gap-4">
      <div class="card border border-base-300 bg-base-200/70">
        <div class="card-body gap-3 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-base-content/70">Agent</h3>
          <label class="form-control">
            <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">Name</span>
            <input
              class="input input-bordered w-full"
              placeholder="Demo Agent"
              value={props.config.agent.name}
              onInput={(event) =>
                updateConfig({
                  ...props.config,
                  agent: {
                    ...props.config.agent,
                    name: event.currentTarget.value,
                  },
                })}
            />
          </label>
          <label class="form-control">
            <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">Model</span>
            <input
              class="input input-bordered w-full"
              placeholder="openrouter:openrouter/free"
              value={props.config.agent.model}
              onInput={(event) =>
                updateConfig({
                  ...props.config,
                  agent: {
                    ...props.config.agent,
                    model: event.currentTarget.value,
                  },
                })}
            />
          </label>
          <label class="form-control">
            <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">
              Instructions
            </span>
            <textarea
              class="textarea textarea-bordered min-h-36 w-full"
              value={props.config.agent.instructions}
              onInput={(event) =>
                updateConfig({
                  ...props.config,
                  agent: {
                    ...props.config.agent,
                    instructions: event.currentTarget.value,
                  },
                })}
            />
          </label>
        </div>
      </div>

      <div class="card border border-base-300 bg-base-200/70">
        <div class="card-body gap-3 p-4">
          <div class="flex items-center justify-between gap-2">
            <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-base-content/70">MCP Servers</h3>
            <button type="button" class="btn btn-sm btn-outline" onClick={addMcpServer}>
              Add Server
            </button>
          </div>
          <Show when={props.config.mcp_servers.length > 0} fallback={<p class="text-sm text-base-content/60">No MCP servers configured.</p>}>
            <div class="grid gap-3">
              <For each={props.config.mcp_servers}>
                {(server, index) => (
                  <div class="grid gap-2 md:grid-cols-[1fr_auto]">
                    <label class="form-control">
                      <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">
                        URL #{index() + 1}
                      </span>
                      <input
                        class="input input-bordered w-full"
                        placeholder="http://127.0.0.1:18001/mcp"
                        value={server.url}
                        onInput={(event) => updateMcpServer(index(), event.currentTarget.value)}
                      />
                    </label>
                    <button type="button" class="btn btn-sm btn-error self-end" onClick={() => removeMcpServer(index())}>
                      Remove
                    </button>
                  </div>
                )}
              </For>
            </div>
          </Show>
        </div>
      </div>
    </div>
  );
}
