import { For } from "solid-js";
import type { ToastMessage } from "~/components/managed-agents/types";

export default function ToastViewport(props: { toasts: ToastMessage[] }) {
  return (
    <div class="toast toast-top toast-end z-50">
      <For each={props.toasts}>
        {(toast) => (
          <div class={`alert ${toast.kind === "error" ? "alert-error" : "alert-success"} shadow-lg`}>
            <span class="text-sm">{toast.message}</span>
          </div>
        )}
      </For>
    </div>
  );
}
