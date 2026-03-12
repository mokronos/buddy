import { For, Show } from "solid-js";
import type { ExternalAgent } from "~/a2a/externalAgents";
import FeedbackAlert from "~/components/managed-agents/FeedbackAlert";
import type { FeedbackState } from "~/components/managed-agents/types";
import Skeleton from "~/components/ui/Skeleton";

function ExternalAgentsLoadingState() {
  return (
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
  );
}

export default function ExternalAgentsSection(props: {
  agents: ExternalAgent[];
  shouldShowLoading: boolean;
  createFeedback: FeedbackState;
  listFeedback: FeedbackState;
  listErrorMessage: string | null;
  editFeedback: FeedbackState;
  externalAgentId: string;
  externalAgentUrl: string;
  externalUseLegacyCardPath: boolean;
  editingExternalAgentId: string | null;
  editingExternalAgentUrl: string;
  editingExternalUseLegacyCardPath: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  onExternalAgentIdChange: (value: string) => void;
  onExternalAgentUrlChange: (value: string) => void;
  onExternalUseLegacyCardPathChange: (value: boolean) => void;
  onEditingExternalAgentUrlChange: (value: string) => void;
  onEditingExternalUseLegacyCardPathChange: (value: boolean) => void;
  onSubmit: (event: SubmitEvent) => void | Promise<void>;
  onBeginEdit: (agent: ExternalAgent) => void;
  onCancelEdit: () => void;
  onSaveEdit: (agentId: string) => void;
  onDelete: (agentId: string) => void;
}) {
  return (
    <>
      <section class="card border border-base-100/10 bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">Add External A2A Agent</h2>
          <p class="mb-4 text-sm text-base-content/70">
            Register an external Buddy-compatible server URL and access it through the local proxy.
          </p>
          <form class="grid gap-3" onSubmit={props.onSubmit}>
            <input
              class="input input-bordered w-full"
              placeholder="External Agent ID (example: remote-buddy)"
              value={props.externalAgentId}
              onInput={(event) => props.onExternalAgentIdChange(event.currentTarget.value)}
            />
            <input
              class="input input-bordered w-full"
              placeholder="Base URL (example: http://192.168.1.20:10001)"
              value={props.externalAgentUrl}
              onInput={(event) => props.onExternalAgentUrlChange(event.currentTarget.value)}
            />
            <label class="label cursor-pointer justify-start gap-3">
              <input
                type="checkbox"
                class="checkbox checkbox-primary"
                checked={props.externalUseLegacyCardPath}
                onChange={(event) => props.onExternalUseLegacyCardPathChange(event.currentTarget.checked)}
              />
              <span class="label-text">Use legacy card path (`/.well-known/agent.json`)</span>
            </label>
            <button type="submit" disabled={props.isCreating} class="btn btn-secondary w-fit">
              {props.isCreating ? (
                <>
                  <span class="loading loading-spinner loading-sm" />
                  Adding...
                </>
              ) : (
                "Add External Agent"
              )}
            </button>
            <FeedbackAlert feedback={props.createFeedback} />
          </form>
        </div>
      </section>

      <section class="card border border-base-100/10 bg-base-100 shadow-xl">
        <div class="card-body">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="card-title">External Agents</h2>
          </div>
          <FeedbackAlert
            feedback={
              props.listFeedback ?? (props.listErrorMessage ? { kind: "error", message: props.listErrorMessage } : null)
            }
            class="mb-3"
          />
          <div class="grid gap-3">
            <Show when={props.shouldShowLoading && props.agents.length === 0}>
              <ExternalAgentsLoadingState />
            </Show>
            <For each={props.agents}>
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
                    <Show
                      when={props.editingExternalAgentId === externalAgent.agent_id}
                      fallback={
                        <div class="join mt-3 flex flex-wrap">
                          <button
                            type="button"
                            class="btn btn-sm join-item"
                            onClick={() => props.onBeginEdit(externalAgent)}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            class="btn btn-sm btn-error join-item"
                            onClick={() => props.onDelete(externalAgent.agent_id)}
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
                            onChange={(event) =>
                              props.onEditingExternalUseLegacyCardPathChange(event.currentTarget.checked)}
                          />
                          <span class="label-text text-xs">Use legacy card path (`/.well-known/agent.json`)</span>
                        </label>
                        <div class="join flex flex-wrap">
                          <button
                            type="button"
                            disabled={props.isUpdating}
                            class="btn btn-sm btn-primary join-item"
                            onClick={() => props.onSaveEdit(externalAgent.agent_id)}
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
              )}
            </For>
            <Show when={props.agents.length === 0 && !props.shouldShowLoading}>
              <p class="text-sm text-base-content/60">0 external agents available.</p>
            </Show>
          </div>
        </div>
      </section>
    </>
  );
}
