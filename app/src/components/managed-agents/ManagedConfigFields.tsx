import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";

export default function ManagedConfigFields(props: {
  config: RuntimeAgentConfigPayload;
  onChange: (config: RuntimeAgentConfigPayload) => void;
  disableAgentId?: boolean;
}) {
  const updateConfig = (nextConfig: RuntimeAgentConfigPayload): void => {
    props.onChange(nextConfig);
  };

  return (
    <div class="grid gap-4">
      <div class="card border border-base-300 bg-base-200/70">
        <div class="card-body gap-3 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-base-content/70">Agent</h3>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="form-control">
              <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">
                Agent ID
              </span>
              <input
                class="input input-bordered w-full"
                placeholder="demo-agent"
                value={props.config.agent.id}
                disabled={props.disableAgentId}
                onInput={(event) =>
                  updateConfig({
                    ...props.config,
                    agent: {
                      ...props.config.agent,
                      id: event.currentTarget.value,
                    },
                  })}
              />
            </label>
            <label class="form-control">
              <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">
                Agent Name
              </span>
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
          </div>
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
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-base-content/70">A2A Runtime</h3>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="form-control">
              <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">Port</span>
              <input
                type="number"
                class="input input-bordered w-full"
                min="1"
                max="65535"
                value={props.config.a2a.port}
                onInput={(event) =>
                  updateConfig({
                    ...props.config,
                    a2a: {
                      ...props.config.a2a,
                      port: Number.parseInt(event.currentTarget.value, 10) || 0,
                    },
                  })}
              />
            </label>
            <label class="form-control">
              <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">
                Mount Path
              </span>
              <input
                class="input input-bordered w-full"
                placeholder="/a2a"
                value={props.config.a2a.mount_path}
                onInput={(event) =>
                  updateConfig({
                    ...props.config,
                    a2a: {
                      ...props.config.a2a,
                      mount_path: event.currentTarget.value,
                    },
                  })}
              />
            </label>
          </div>
        </div>
      </div>

      <div class="card border border-base-300 bg-base-200/70">
        <div class="card-body gap-3 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-base-content/70">Tools</h3>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="label cursor-pointer justify-start gap-3 rounded-box border border-base-300 px-4 py-3">
              <input
                type="checkbox"
                class="checkbox checkbox-primary"
                checked={props.config.tools.web_search}
                onChange={(event) =>
                  updateConfig({
                    ...props.config,
                    tools: {
                      ...props.config.tools,
                      web_search: event.currentTarget.checked,
                    },
                  })}
              />
              <div>
                <span class="block text-sm font-medium">Web Search</span>
                <span class="text-xs text-base-content/60">Allow the built-in web search tools.</span>
              </div>
            </label>
            <label class="label cursor-pointer justify-start gap-3 rounded-box border border-base-300 px-4 py-3">
              <input
                type="checkbox"
                class="checkbox checkbox-primary"
                checked={props.config.tools.todo}
                onChange={(event) =>
                  updateConfig({
                    ...props.config,
                    tools: {
                      ...props.config.tools,
                      todo: event.currentTarget.checked,
                    },
                  })}
              />
              <div>
                <span class="block text-sm font-medium">Todo</span>
                <span class="text-xs text-base-content/60">Enable the built-in todo list tools.</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      <div class="card border border-base-300 bg-base-200/70">
        <div class="card-body gap-3 p-4">
          <h3 class="text-sm font-semibold uppercase tracking-[0.2em] text-base-content/70">MCP</h3>
          <label class="label cursor-pointer justify-start gap-3 rounded-box border border-base-300 px-4 py-3">
            <input
              type="checkbox"
              class="checkbox checkbox-primary"
              checked={props.config.mcp.enabled}
              onChange={(event) =>
                updateConfig({
                  ...props.config,
                  mcp: {
                    ...props.config.mcp,
                    enabled: event.currentTarget.checked,
                  },
                })}
            />
            <div>
              <span class="block text-sm font-medium">Enable MCP Server</span>
              <span class="text-xs text-base-content/60">Connect the runtime to the configured MCP endpoint.</span>
            </div>
          </label>
          <label class="form-control">
            <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">MCP URL</span>
            <input
              class="input input-bordered w-full"
              placeholder="http://127.0.0.1:18001/mcp"
              value={props.config.mcp.url}
              disabled={!props.config.mcp.enabled}
              onInput={(event) =>
                updateConfig({
                  ...props.config,
                  mcp: {
                    ...props.config.mcp,
                    url: event.currentTarget.value,
                  },
                })}
            />
          </label>
        </div>
      </div>
    </div>
  );
}
