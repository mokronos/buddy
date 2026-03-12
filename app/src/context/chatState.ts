import { type Setter } from "solid-js";
import type { A2AClient } from "~/a2a/client";
import type { Message } from "~/data/sampleMessages";

export interface AgentConversationState {
  messages: Message[];
  isSending: boolean;
  isCancelling: boolean;
  activeRequestTaskId: string | null;
  contextId: string | null;
  label: string;
}

export interface AgentWorkspaceState {
  tasks: Record<string, AgentConversationState>;
  taskOrder: string[];
  nextTaskNumber: number;
}

export interface ActiveChatRequest {
  abortController: AbortController;
  client: A2AClient;
  requestTaskId: string | null;
  cancelRequested: boolean;
  cancellationConfirmed: boolean;
  cancelState: "idle" | "requested" | "not-cancelable" | "timed-out" | "failed";
  failureMessage: string | null;
  cancelPromise: Promise<void> | null;
}

function toSlug(value: string): string {
  const slug = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug.length > 0 ? slug : "agent";
}

export function timestamp(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function buildAgentContextId(agentKey: string): string {
  return `agent-${toSlug(agentKey)}--${crypto.randomUUID()}`;
}

export function buildRequestKey(agentKey: string, taskId: string): string {
  return `${agentKey}::${taskId}`;
}

export function emptyConversation(label: string, messages: Message[] = []): AgentConversationState {
  return {
    messages,
    isSending: false,
    isCancelling: false,
    activeRequestTaskId: null,
    contextId: null,
    label,
  };
}

export function createWorkspace(initialMessages: Message[] = []): AgentWorkspaceState {
  const defaultTaskId = "task-1";
  return {
    tasks: {
      [defaultTaskId]: emptyConversation("Task 1", initialMessages),
    },
    taskOrder: [defaultTaskId],
    nextTaskNumber: 2,
  };
}

export function upsertAIMessage(
  setMessages: Setter<Message[]>,
  id: string,
  content: string,
  timestampValue: string,
): void {
  setMessages((current) => {
    const existingIndex = current.findIndex((message) => message.id === id);

    if (existingIndex === -1) {
      return [
        ...current,
        {
          id,
          type: "ai",
          content,
          timestamp: timestampValue,
        },
      ];
    }

    const updated = [...current];
    updated[existingIndex] = {
      ...updated[existingIndex],
      content,
      type: "ai",
    };
    return updated;
  });
}

export function upsertThinkingMessage(
  setMessages: Setter<Message[]>,
  id: string,
  content: string,
  timestampValue: string,
): void {
  setMessages((current) => {
    const existingIndex = current.findIndex((message) => message.id === id);

    if (existingIndex === -1) {
      return [
        ...current,
        {
          id,
          type: "thinking",
          content,
          timestamp: timestampValue,
        },
      ];
    }

    const updated = [...current];
    updated[existingIndex] = {
      ...updated[existingIndex],
      content,
      type: "thinking",
    };
    return updated;
  });
}
