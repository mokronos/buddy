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
            Configure the agent behavior only. Runtime image, mount path, A2A path, ports, tools, and agent id are
            generated automatically.
          </p>
        </div>
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
