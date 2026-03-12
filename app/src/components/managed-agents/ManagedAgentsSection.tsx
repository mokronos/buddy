import { For, Show } from "solid-js";
import type { ExternalAgent } from "~/a2a/externalAgents";
import type { ManagedAgent } from "~/a2a/managedAgents";
import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";
import ManagedConfigFields from "~/components/managed-agents/ManagedConfigFields";
import Skeleton from "~/components/ui/Skeleton";

function ManagedAgentsLoadingState() {
  return (
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
  );
}

function ManagedAgentCard(props: {
  agent: ManagedAgent;
  isDeleting: boolean;
  isEditing: boolean;
  editingConfig: RuntimeAgentConfigPayload | null;
  restartAfterSave: boolean;
  isSavingEdit: boolean;
  onStart: (agentId: string) => void;
  onStop: (agentId: string) => void;
  onBeginEdit: (agentId: string) => void;
  onDelete: (agentId: string) => void;
  onEditingConfigChange: (config: RuntimeAgentConfigPayload) => void;
  onRestartAfterSaveChange: (value: boolean) => void;
  onSaveEdit: (agentId: string) => void;
  onCancelEdit: () => void;
}) {
  const shortModel = (): string => {
    const model = props.agent.config?.agent.model ?? "";
    if (model.length <= 40) {
      return model;
    }
    return `${model.slice(0, 40)}...`;
  };

  const mcpCount = (): number => props.agent.config?.mcp_servers.length ?? 0;

  const instructionPreview = (): string => {
    const instructions = props.agent.config?.agent.instructions ?? "";
    if (instructions.length <= 180) {
      return instructions;
    }
    return `${instructions.slice(0, 180)}...`;
  };

  return (
    <article class="card border border-base-300 bg-base-100 shadow-sm transition-shadow hover:shadow-md">
      <div class="card-body gap-3 p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="card-title truncate text-base">{props.agent.config?.agent.name ?? props.agent.agent_id}</h3>
            <p class="truncate text-xs text-base-content/60">{props.agent.agent_id}</p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <span class="badge badge-primary badge-outline">managed</span>
            <span class={`badge badge-outline ${props.isDeleting ? "badge-warning" : "badge-neutral"}`}>
              {props.isDeleting ? "deleting" : props.agent.status}
            </span>
          </div>
        </div>

        <div class="flex flex-wrap gap-2 text-xs">
          <Show when={shortModel().length > 0} fallback={<span class="badge badge-ghost">model: -</span>}>
            <span class="badge badge-ghost">model: {shortModel()}</span>
          </Show>
          <span class="badge badge-ghost">mcp: {mcpCount()}</span>
        </div>

        <div class="grid gap-2 text-xs text-base-content/70">
          <Show when={instructionPreview().length > 0}>
            <div class="rounded-box border border-base-300 bg-base-200/60 px-3 py-2">
              <p class="font-medium text-base-content/80">Instructions</p>
              <p class="mt-1 leading-relaxed">{instructionPreview()}</p>
            </div>
          </Show>
          {props.agent.last_error ? <p class="rounded-box bg-error/10 px-3 py-2 text-error">{props.agent.last_error}</p> : null}
          {props.isDeleting ? (
            <p class="inline-flex items-center gap-2 text-warning">
              <span class="loading loading-spinner loading-xs" />
              Waiting for container shutdown...
            </p>
          ) : null}
        </div>

        <div class="join flex flex-wrap">
          <button
            type="button"
            disabled={props.isDeleting}
            class="btn btn-sm join-item"
            onClick={() => props.onStart(props.agent.agent_id)}
          >
            Start
          </button>
          <button
            type="button"
            disabled={props.isDeleting}
            class="btn btn-sm join-item"
            onClick={() => props.onStop(props.agent.agent_id)}
          >
            Stop
          </button>
          <button
            type="button"
            disabled={props.isDeleting}
            class="btn btn-sm join-item"
            onClick={() => props.onBeginEdit(props.agent.agent_id)}
          >
            Edit Config
          </button>
          <button
            type="button"
            disabled={props.isDeleting}
            class="btn btn-sm btn-error join-item"
            onClick={() => props.onDelete(props.agent.agent_id)}
          >
            {props.isDeleting ? "Deleting..." : "Delete"}
          </button>
        </div>
        <Show when={props.isEditing && props.editingConfig}>
          {(config) => (
            <div class="mt-1 grid gap-3 rounded-box border border-base-300 bg-base-200/60 p-3">
              <ManagedConfigFields
                config={config()}
                onChange={(nextConfig) => props.onEditingConfigChange(nextConfig)}
              />
              <label class="label cursor-pointer justify-start gap-3">
                <input
                  type="checkbox"
                  class="checkbox checkbox-primary checkbox-sm"
                  checked={props.restartAfterSave}
                  onChange={(event) => props.onRestartAfterSaveChange(event.currentTarget.checked)}
                />
                <span class="label-text text-xs">Restart container after save</span>
              </label>
              <div class="join flex flex-wrap">
                <button
                  type="button"
                  disabled={props.isSavingEdit || props.isDeleting}
                  class="btn btn-sm btn-primary join-item"
                  onClick={() => props.onSaveEdit(props.agent.agent_id)}
                >
                  {props.isSavingEdit ? (
                    <>
                      <span class="loading loading-spinner loading-xs" />
                      Saving...
                    </>
                  ) : (
                    "Save"
                  )}
                </button>
                <button
                  type="button"
                  disabled={props.isDeleting}
                  class="btn btn-sm join-item"
                  onClick={props.onCancelEdit}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </Show>
      </div>
    </article>
  );
}

function ExternalAgentCard(props: {
  agent: ExternalAgent;
  isEditing: boolean;
  isUpdating: boolean;
  editingExternalAgentUrl: string;
  editingExternalUseLegacyCardPath: boolean;
  onBeginEdit: (agent: ExternalAgent) => void;
  onDelete: (agentId: string) => void;
  onEditingExternalAgentUrlChange: (value: string) => void;
  onEditingExternalUseLegacyCardPathChange: (value: boolean) => void;
  onSaveEdit: (agentId: string) => void;
  onCancelEdit: () => void;
}) {
  return (
    <article class="card border border-base-300 bg-base-100 shadow-sm transition-shadow hover:shadow-md">
      <div class="card-body gap-3 p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <h3 class="card-title truncate text-base">{props.agent.agent_id}</h3>
            <p class="truncate text-xs text-base-content/60">{props.agent.base_url}</p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <span class="badge badge-secondary badge-outline">external</span>
            <span class="badge badge-neutral badge-outline">registered</span>
          </div>
        </div>
        <div class="flex flex-wrap gap-2 text-xs">
          <span class="badge badge-ghost">
            legacy card path: {props.agent.use_legacy_card_path ? "enabled" : "disabled"}
          </span>
        </div>

        <Show
          when={props.isEditing}
          fallback={
            <div class="join flex flex-wrap">
              <button type="button" class="btn btn-sm join-item" onClick={() => props.onBeginEdit(props.agent)}>
                Edit
              </button>
              <button
                type="button"
                class="btn btn-sm btn-error join-item"
                onClick={() => props.onDelete(props.agent.agent_id)}
              >
                Delete
              </button>
            </div>
          }
        >
          <div class="grid gap-2 rounded-box border border-base-300 bg-base-200/60 p-3">
            <input
              class="input input-bordered w-full text-xs"
              value={props.editingExternalAgentUrl}
              onInput={(event) => props.onEditingExternalAgentUrlChange(event.currentTarget.value)}
            />
            <label class="label cursor-pointer justify-start gap-3">
              <input
                type="checkbox"
                class="checkbox checkbox-primary checkbox-sm"
                checked={props.editingExternalUseLegacyCardPath}
                onChange={(event) => props.onEditingExternalUseLegacyCardPathChange(event.currentTarget.checked)}
              />
              <span class="label-text text-xs">Use legacy card path (`/.well-known/agent.json`)</span>
            </label>
            <div class="join flex flex-wrap">
              <button
                type="button"
                disabled={props.isUpdating}
                class="btn btn-sm btn-primary join-item"
                onClick={() => props.onSaveEdit(props.agent.agent_id)}
              >
                {props.isUpdating ? (
                  <>
                    <span class="loading loading-spinner loading-xs" />
                    Saving...
                  </>
                ) : (
                  "Save"
                )}
              </button>
              <button type="button" class="btn btn-sm join-item" onClick={props.onCancelEdit}>
                Cancel
              </button>
            </div>
          </div>
        </Show>
      </div>
    </article>
  );
}

export default function ManagedAgentsSection(props: {
  managedAgents: ManagedAgent[];
  externalAgents: ExternalAgent[];
  shouldShowLoading: boolean;
  editingManagedAgentId: string | null;
  editingExternalAgentId: string | null;
  editingManagedConfig: RuntimeAgentConfigPayload | null;
  editingExternalAgentUrl: string;
  editingExternalUseLegacyCardPath: boolean;
  restartAfterSave: boolean;
  isSavingManagedEdit: boolean;
  isSavingExternalEdit: boolean;
  isDeletingManagedAgent: (agentId: string) => boolean;
  onRefresh: () => void;
  onStartManaged: (agentId: string) => void;
  onStopManaged: (agentId: string) => void;
  onBeginEditManaged: (agentId: string) => void;
  onDeleteManaged: (agentId: string) => void;
  onEditingManagedConfigChange: (config: RuntimeAgentConfigPayload) => void;
  onRestartAfterSaveChange: (value: boolean) => void;
  onSaveManagedEdit: (agentId: string) => void;
  onCancelManagedEdit: () => void;
  onBeginEditExternal: (agent: ExternalAgent) => void;
  onDeleteExternal: (agentId: string) => void;
  onEditingExternalAgentUrlChange: (value: string) => void;
  onEditingExternalUseLegacyCardPathChange: (value: boolean) => void;
  onSaveExternalEdit: (agentId: string) => void;
  onCancelExternalEdit: () => void;
}) {
  const totalAgents = (): number => props.managedAgents.length + props.externalAgents.length;

  return (
    <section class="card h-full min-h-0 border border-base-100/10 bg-base-100 shadow-xl">
      <div class="card-body flex h-full min-h-0">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="card-title">Current Agents</h2>
          <button type="button" class="btn btn-sm btn-outline" onClick={props.onRefresh}>
            Refresh
          </button>
        </div>

        <div class="grid min-h-0 flex-1 gap-3 overflow-y-auto pr-1">
          <Show when={props.shouldShowLoading && totalAgents() === 0}>
            <ManagedAgentsLoadingState />
          </Show>
          <For each={props.managedAgents}>
            {(agent) => (
              <ManagedAgentCard
                agent={agent}
                isDeleting={props.isDeletingManagedAgent(agent.agent_id)}
                isEditing={props.editingManagedAgentId === agent.agent_id}
                editingConfig={props.editingManagedConfig}
                restartAfterSave={props.restartAfterSave}
                isSavingEdit={props.isSavingManagedEdit}
                onStart={props.onStartManaged}
                onStop={props.onStopManaged}
                onBeginEdit={props.onBeginEditManaged}
                onDelete={props.onDeleteManaged}
                onEditingConfigChange={props.onEditingManagedConfigChange}
                onRestartAfterSaveChange={props.onRestartAfterSaveChange}
                onSaveEdit={props.onSaveManagedEdit}
                onCancelEdit={props.onCancelManagedEdit}
              />
            )}
          </For>
          <For each={props.externalAgents}>
            {(agent) => (
              <ExternalAgentCard
                agent={agent}
                isEditing={props.editingExternalAgentId === agent.agent_id}
                isUpdating={props.isSavingExternalEdit}
                editingExternalAgentUrl={props.editingExternalAgentUrl}
                editingExternalUseLegacyCardPath={props.editingExternalUseLegacyCardPath}
                onBeginEdit={props.onBeginEditExternal}
                onDelete={props.onDeleteExternal}
                onEditingExternalAgentUrlChange={props.onEditingExternalAgentUrlChange}
                onEditingExternalUseLegacyCardPathChange={props.onEditingExternalUseLegacyCardPathChange}
                onSaveEdit={props.onSaveExternalEdit}
                onCancelEdit={props.onCancelExternalEdit}
              />
            )}
          </For>
          <Show when={totalAgents() === 0 && !props.shouldShowLoading}>
            <p class="text-sm text-base-content/60">0 agents available.</p>
          </Show>
        </div>
      </div>
    </section>
  );
}
