import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";

export type FeedbackState =
  | {
      kind: "error" | "success";
      message: string;
    }
  | null;

export interface ManagedCreateFormState {
  image: string;
  config_mount_path: string;
  config: RuntimeAgentConfigPayload;
}
