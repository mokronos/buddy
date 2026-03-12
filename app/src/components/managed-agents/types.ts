import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";

export type FeedbackState =
  | {
      kind: "error" | "success";
      message: string;
    }
  | null;

export interface ToastInput {
  kind: "error" | "success";
  message: string;
}

export interface ToastMessage extends ToastInput {
  id: number;
}

export interface ManagedCreateFormState {
  config: RuntimeAgentConfigPayload;
}
