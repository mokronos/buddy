import { Show } from "solid-js";
import type { FeedbackState } from "~/components/managed-agents/types";

export default function FeedbackAlert(props: { feedback: FeedbackState; class?: string }) {
  return (
    <Show when={props.feedback}>
      {(feedback) => {
        const alertClass = feedback().kind === "error" ? "alert-error" : "alert-success";
        return <p class={`alert ${alertClass} text-sm ${props.class ?? ""}`}>{feedback().message}</p>;
      }}
    </Show>
  );
}
