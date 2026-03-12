import { For, Show } from "solid-js";
import type { ExternalAgent } from "~/a2a/externalAgents";
import type { ManagedAgent } from "~/a2a/managedAgents";
import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";
import FeedbackAlert from "~/components/managed-agents/FeedbackAlert";
import ManagedConfigFields from "~/components/managed-agents/ManagedConfigFields";
import type { FeedbackState } from "~/components/managed-agents/types";
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
  editFeedback: FeedbackState;
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
  return (
    <article class="card border border-base-300 bg-base-200 shadow-sm">
      <div class="card-body p-4">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p class="font-medium">{props.agent.agent_id}</p>
            <p class="text-xs text-base-content/60">{props.agent.image}</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="badge badge-primary badge-outline">managed</span>
            <span class={`badge badge-outline ${props.isDeleting ? "badge-warning" : "badge-neutral"}`}>
              {props.isDeleting ? "deleting" : props.agent.status}
            </span>
          </div>
        </div>
        <div class="mt-2 grid gap-1 text-xs text-base-content/60 md:grid-cols-2">
          <p>container: {props.agent.container_id ?? "-"}</p>
          <p>host port: {props.agent.host_port ?? "-"}</p>
          <p>runtime port: {props.agent.container_port}</p>
          <p>runtime path: {props.agent.a2a_mount_path}</p>
          <p>config mount: {props.agent.config_mount_path}</p>
          <p>config file: {props.agent.config_path}</p>
          {props.agent.last_error ? <p class="text-error md:col-span-2">error: {props.agent.last_error}</p> : null}
          {props.isDeleting ? (
            <p class="inline-flex items-center gap-2 text-warning md:col-span-2">
              <span class="loading loading-spinner loading-xs" />
              Waiting for container shutdown...
            </p>
          ) : null}
        </div>
        <div class="join mt-3 flex flex-wrap">
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
            <div class="mt-4 grid gap-3">
              <ManagedConfigFields
                config={config()}
                onChange={(nextConfig) => props.onEditingConfigChange(nextConfig)}
              />
              <FeedbackAlert feedback={props.editFeedback} />
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
                  Save Config
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
  editFeedback: FeedbackState;
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
    <article class="card border border-base-300 bg-base-200 shadow-sm">
      <div class="card-body p-4">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p class="font-medium">{props.agent.agent_id}</p>
            <p class="text-xs text-base-content/60">{props.agent.base_url}</p>
          </div>
          <div class="flex items-center gap-2">
            <span class="badge badge-secondary badge-outline">external</span>
            <span class="badge badge-neutral badge-outline">registered</span>
          </div>
        </div>
        <div class="mt-2 text-xs text-base-content/60">
          <p>proxy: /a2a/external/{props.agent.agent_id}</p>
          <p>card path: {props.agent.use_legacy_card_path ? "legacy" : "standard"}</p>
        </div>
        <Show
          when={props.isEditing}
          fallback={
            <div class="join mt-3 flex flex-wrap">
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
          <div class="mt-3 grid gap-2">
            <input
              class="input input-bordered w-full text-xs"
              value={props.editingExternalAgentUrl}
              onInput={(event) => props.onEditingExternalAgentUrlChange(event.currentTarget.value)}
            />
            <FeedbackAlert feedback={props.editFeedback} />
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
                Save
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
  managedListFeedback: FeedbackState;
  externalListFeedback: FeedbackState;
  listErrorMessage: string | null;
  managedEditFeedback: FeedbackState;
  externalEditFeedback: FeedbackState;
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
  const listFeedback = (): FeedbackState => props.managedListFeedback ?? props.externalListFeedback;
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

        <FeedbackAlert
          feedback={listFeedback() ?? (props.listErrorMessage ? { kind: "error", message: props.listErrorMessage } : null)}
          class="mb-3"
        />

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
                editFeedback={props.managedEditFeedback}
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
                editFeedback={props.externalEditFeedback}
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
