import type { MessageSendParams } from "@a2a-js/sdk";
import type { A2AStreamEvent } from "~/a2a/client";

export const CANCEL_TIMEOUT_MS = 5000;
export const CANCELLATION_TIMEOUT_MESSAGE = "Cancellation request timed out. The local stream was stopped.";

export function createTextMessageParams(text: string, contextId: string): MessageSendParams {
  return {
    message: {
      kind: "message",
      messageId: crypto.randomUUID(),
      contextId,
      role: "user",
      parts: [{ kind: "text", text }],
    },
  };
}

export function readTextParts(value: unknown): string {
  if (!Array.isArray(value)) {
    return "";
  }

  return value
    .map((part) => {
      if (!part || typeof part !== "object") {
        return "";
      }

      const candidate = part as { kind?: unknown; text?: unknown };
      return candidate.kind === "text" && typeof candidate.text === "string" ? candidate.text : "";
    })
    .filter((entry) => entry.length > 0)
    .join("\n");
}

export function readDataParts(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((part) => {
      if (!part || typeof part !== "object") {
        return null;
      }

      const candidate = part as { kind?: unknown; data?: unknown };
      if (candidate.kind !== "data") {
        return null;
      }

      if (!candidate.data || typeof candidate.data !== "object" || Array.isArray(candidate.data)) {
        return null;
      }

      return candidate.data as Record<string, unknown>;
    })
    .filter((entry): entry is Record<string, unknown> => entry !== null);
}

export function toPrettyText(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

export function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

export function isTaskNotCancelableError(error: unknown): boolean {
  if (!(error instanceof Error)) {
    return false;
  }

  const message = error.message.toLowerCase();
  return (
    error.name === "TaskNotCancelableError" ||
    message.includes("task not cancelable") ||
    message.includes("task cannot be canceled")
  );
}

export function readEventTaskId(event: A2AStreamEvent): string | null {
  const payload = event as { taskId?: unknown; id?: unknown };
  if (typeof payload.taskId === "string" && payload.taskId.length > 0) {
    return payload.taskId;
  }
  if (event.kind === "task" && typeof payload.id === "string" && payload.id.length > 0) {
    return payload.id;
  }
  return null;
}

export function readEventStatusState(event: A2AStreamEvent): string | null {
  if (event.kind === "status-update") {
    const payload = event as { status?: { state?: unknown } };
    return typeof payload.status?.state === "string" ? payload.status.state : null;
  }
  if (event.kind === "task") {
    const payload = event as { status?: { state?: unknown } };
    return typeof payload.status?.state === "string" ? payload.status.state : null;
  }
  return null;
}
