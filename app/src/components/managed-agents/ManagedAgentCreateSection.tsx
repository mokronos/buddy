import { Show, createSignal } from "solid-js";
import type { ManagedCreateFormState } from "~/components/managed-agents/types";
import ManagedConfigFields from "~/components/managed-agents/ManagedConfigFields";

export default function ManagedAgentCreateSection(props: {
  form: ManagedCreateFormState;
  onFormChange: (nextForm: ManagedCreateFormState) => void;
  onSubmit: (event: SubmitEvent) => void | Promise<void>;
  isSubmitting: boolean;
  externalAgentId: string;
  externalAgentUrl: string;
  externalUseLegacyCardPath: boolean;
  isExternalSubmitting: boolean;
  onExternalAgentIdChange: (value: string) => void;
  onExternalAgentUrlChange: (value: string) => void;
  onExternalUseLegacyCardPathChange: (value: boolean) => void;
  onExternalSubmit: (event: SubmitEvent) => void | Promise<void>;
}) {
  const [activeTab, setActiveTab] = createSignal<"managed" | "external">("managed");

  return (
    <section class="card h-full min-h-0 border border-base-100/10 bg-base-100 shadow-xl">
      <div class="card-body min-h-0 gap-4 overflow-y-auto">
        <div>
          <h2 class="card-title">Add Agent</h2>
          <p class="mt-1 text-sm text-base-content/70">
            Add either a managed runtime agent or an external proxy agent. Runtime image, mount path, A2A path, ports,
            tools, and agent id are
            generated automatically.
          </p>
        </div>
        <div role="tablist" class="tabs tabs-box w-fit">
          <button
            type="button"
            role="tab"
            class={`tab ${activeTab() === "managed" ? "tab-active" : ""}`}
            onClick={() => setActiveTab("managed")}
          >
            Managed
          </button>
          <button
            type="button"
            role="tab"
            class={`tab ${activeTab() === "external" ? "tab-active" : ""}`}
            onClick={() => setActiveTab("external")}
          >
            External
          </button>
        </div>

        <Show when={activeTab() === "managed"}>
          <form class="grid gap-4" onSubmit={props.onSubmit}>
            <ManagedConfigFields
              config={props.form.config}
              onChange={(config) =>
                props.onFormChange({
                  ...props.form,
                  config,
                })}
            />
            <button type="submit" disabled={props.isSubmitting} class="btn btn-primary w-fit">
              {props.isSubmitting ? (
                <>
                  <span class="loading loading-spinner loading-sm" />
                  Adding...
                </>
              ) : (
                "Add"
              )}
            </button>
          </form>
        </Show>

        <Show when={activeTab() === "external"}>
          <form class="grid gap-3" onSubmit={props.onExternalSubmit}>
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
            <button type="submit" disabled={props.isExternalSubmitting} class="btn btn-primary w-fit">
              {props.isExternalSubmitting ? (
                <>
                  <span class="loading loading-spinner loading-sm" />
                  Adding...
                </>
              ) : (
                "Add"
              )}
            </button>
          </form>
        </Show>
      </div>
    </section>
  );
}
