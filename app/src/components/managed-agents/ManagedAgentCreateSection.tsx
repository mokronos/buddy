import type { ManagedCreateFormState, FeedbackState } from "~/components/managed-agents/types";
import FeedbackAlert from "~/components/managed-agents/FeedbackAlert";
import ManagedConfigFields from "~/components/managed-agents/ManagedConfigFields";

export default function ManagedAgentCreateSection(props: {
  form: ManagedCreateFormState;
  onFormChange: (nextForm: ManagedCreateFormState) => void;
  onSubmit: (event: SubmitEvent) => void | Promise<void>;
  isSubmitting: boolean;
  feedback: FeedbackState;
}) {
  return (
    <section class="card border border-base-100/10 bg-base-100 shadow-xl">
      <div class="card-body gap-4">
        <div>
          <h2 class="card-title">Create Agent</h2>
          <p class="mt-1 text-sm text-base-content/70">
            The runtime config below is the source of truth for agent identity, A2A server settings, tools, and MCP
            connectivity.
          </p>
        </div>
        <form class="grid gap-4" onSubmit={props.onSubmit}>
          <div class="grid gap-3 md:grid-cols-2">
            <label class="form-control">
              <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">
                Runtime Image
              </span>
              <input
                class="input input-bordered w-full"
                value={props.form.image}
                onInput={(event) =>
                  props.onFormChange({
                    ...props.form,
                    image: event.currentTarget.value,
                  })}
              />
            </label>
            <label class="form-control">
              <span class="label-text text-xs font-medium uppercase tracking-wide text-base-content/60">
                Config Mount Path
              </span>
              <input
                class="input input-bordered w-full"
                value={props.form.config_mount_path}
                onInput={(event) =>
                  props.onFormChange({
                    ...props.form,
                    config_mount_path: event.currentTarget.value,
                  })}
              />
            </label>
          </div>
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
                Creating...
              </>
            ) : (
              "Create and Start"
            )}
          </button>
          <FeedbackAlert feedback={props.feedback} />
        </form>
      </div>
    </section>
  );
}
