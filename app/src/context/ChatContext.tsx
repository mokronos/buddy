import type { MessageSendParams } from "@a2a-js/sdk";
import {
  createContext,
  createEffect,
  createMemo,
  createSignal,
  useContext,
  type Accessor,
  type JSX,
  type Setter,
} from "solid-js";
import { createA2AClient, type A2AClient, type A2AStreamEvent } from "~/a2a/client";
import { useAgents } from "~/context/AgentsContext";
import type { Message } from "~/data/sampleMessages";

interface ChatContextValue {
  messages: Accessor<Message[]>;
  sendMessage: (content: string) => Promise<void>;
  cancelActiveRequest: () => Promise<void>;
  isSending: Accessor<boolean>;
  isCancelling: Accessor<boolean>;
  tasks: Accessor<{ id: string; label: string; isSending: boolean }[]>;
  activeTaskId: Accessor<string>;
  setActiveTaskId: (taskId: string) => void;
  createTask: () => void;
}

const ChatContext = createContext<ChatContextValue>();
const CANCEL_TIMEOUT_MS = 5000;
const CANCELLATION_TIMEOUT_MESSAGE = "Cancellation request timed out. The local stream was stopped.";

function createTextMessageParams(text: string, contextId: string, taskId: string): MessageSendParams {
  return {
    message: {
      kind: "message",
      messageId: crypto.randomUUID(),
      contextId,
      taskId,
      role: "user",
      parts: [{ kind: "text", text }],
    },
  };
}

function timestamp(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function toSlug(value: string): string {
  const slug = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug.length > 0 ? slug : "agent";
}

function buildAgentContextId(agentKey: string): string {
  return `agent-${toSlug(agentKey)}--${crypto.randomUUID()}`;
}

function buildRequestKey(agentKey: string, taskId: string): string {
  return `${agentKey}::${taskId}`;
}

function readTextParts(value: unknown): string {
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

function readDataParts(value: unknown): Record<string, unknown>[] {
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

function toPrettyText(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function isTaskNotCancelableError(error: unknown): boolean {
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

function readEventTaskId(event: A2AStreamEvent): string | null {
  const payload = event as { taskId?: unknown; id?: unknown };
  if (typeof payload.taskId === "string" && payload.taskId.length > 0) {
    return payload.taskId;
  }
  if (event.kind === "task" && typeof payload.id === "string" && payload.id.length > 0) {
    return payload.id;
  }
  return null;
}

function readEventStatusState(event: A2AStreamEvent): string | null {
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

interface AgentConversationState {
  messages: Message[];
  isSending: boolean;
  isCancelling: boolean;
  activeRequestTaskId: string | null;
  contextId: string | null;
  label: string;
}

interface AgentWorkspaceState {
  tasks: Record<string, AgentConversationState>;
  taskOrder: string[];
  nextTaskNumber: number;
}

function emptyConversation(label: string, messages: Message[] = []): AgentConversationState {
  return {
    messages,
    isSending: false,
    isCancelling: false,
    activeRequestTaskId: null,
    contextId: null,
    label,
  };
}

interface ActiveChatRequest {
  abortController: AbortController;
  client: A2AClient;
  requestTaskId: string;
  cancelRequested: boolean;
  cancellationConfirmed: boolean;
  cancelState: "idle" | "requested" | "not-cancelable" | "timed-out" | "failed";
  failureMessage: string | null;
  cancelPromise: Promise<void> | null;
}

function createWorkspace(initialMessages: Message[] = []): AgentWorkspaceState {
  const defaultTaskId = "task-1";
  return {
    tasks: {
      [defaultTaskId]: emptyConversation("Task 1", initialMessages),
    },
    taskOrder: [defaultTaskId],
    nextTaskNumber: 2,
  };
}

function upsertAIMessage(
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

function upsertThinkingMessage(
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

export function ChatProvider(props: { children: JSX.Element; messages: Message[] }) {
  const { agents, activeAgentKey, refreshAgents } = useAgents();
  const [workspaces, setWorkspaces] = createSignal<Record<string, AgentWorkspaceState>>({});
  const [activeTaskIds, setActiveTaskIds] = createSignal<Record<string, string>>({});
  const activeRequests = new Map<string, ActiveChatRequest>();

  const messages = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = workspaces()[activeKey];
    if (!workspace) {
      return [];
    }
    const selectedTaskId = activeTaskIds()[activeKey] ?? workspace.taskOrder[0] ?? "";
    return workspace.tasks[selectedTaskId]?.messages ?? [];
  });

  const isSending = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = workspaces()[activeKey];
    if (!workspace) {
      return false;
    }
    const selectedTaskId = activeTaskIds()[activeKey] ?? workspace.taskOrder[0] ?? "";
    return workspace.tasks[selectedTaskId]?.isSending ?? false;
  });

  const isCancelling = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = workspaces()[activeKey];
    if (!workspace) {
      return false;
    }
    const selectedTaskId = activeTaskIds()[activeKey] ?? workspace.taskOrder[0] ?? "";
    return workspace.tasks[selectedTaskId]?.isCancelling ?? false;
  });

  const activeTaskId = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = workspaces()[activeKey];
    if (!workspace) {
      return "";
    }
    return activeTaskIds()[activeKey] ?? workspace.taskOrder[0] ?? "";
  });

  const tasks = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = workspaces()[activeKey];
    if (!workspace) {
      return [];
    }

    return workspace.taskOrder
      .map((taskId) => {
        const task = workspace.tasks[taskId];
        if (!task) {
          return null;
        }
        return {
          id: taskId,
          label: task.label,
          isSending: task.isSending,
        };
      })
      .filter((task): task is { id: string; label: string; isSending: boolean } => task !== null);
  });

  const updateWorkspace = (
    agentKey: string,
    updater: (current: AgentWorkspaceState) => AgentWorkspaceState,
  ): AgentWorkspaceState => {
    let nextValue = createWorkspace();
    setWorkspaces((current) => {
      const existing = current[agentKey] ?? createWorkspace();
      nextValue = updater(existing);
      return {
        ...current,
        [agentKey]: nextValue,
      };
    });
    return nextValue;
  };

  const updateTask = (
    agentKey: string,
    taskId: string,
    updater: (current: AgentConversationState) => AgentConversationState,
  ): AgentConversationState => {
    let nextTask = emptyConversation("Task");
    updateWorkspace(agentKey, (workspace) => {
      const currentTask = workspace.tasks[taskId] ?? emptyConversation("Task");
      nextTask = updater(currentTask);
      return {
        ...workspace,
        tasks: {
          ...workspace.tasks,
          [taskId]: nextTask,
        },
      };
    });
    return nextTask;
  };

  createEffect(() => {
    const targetAgentKey = activeAgentKey();
    if (!targetAgentKey) {
      return;
    }

    setWorkspaces((current) => {
      if (current[targetAgentKey]) {
        return current;
      }
      return {
        ...current,
        [targetAgentKey]: createWorkspace(props.messages || []),
      };
    });

    setActiveTaskIds((current) => {
      if (current[targetAgentKey]) {
        return current;
      }
      return {
        ...current,
        [targetAgentKey]: "task-1",
      };
    });
  });

  const setActiveTaskId = (taskId: string): void => {
    const targetAgentKey = activeAgentKey();
    const workspace = workspaces()[targetAgentKey];
    if (!workspace || !workspace.tasks[taskId]) {
      return;
    }
    setActiveTaskIds((current) => {
      if (current[targetAgentKey] === taskId) {
        return current;
      }
      return {
        ...current,
        [targetAgentKey]: taskId,
      };
    });
  };

  const createTask = (): void => {
    const targetAgentKey = activeAgentKey();
    if (!targetAgentKey) {
      return;
    }

    let nextTaskId = "";
    updateWorkspace(targetAgentKey, (workspace) => {
      const taskId = `task-${workspace.nextTaskNumber}`;
      nextTaskId = taskId;
      return {
        ...workspace,
        tasks: {
          ...workspace.tasks,
          [taskId]: emptyConversation(`Task ${workspace.nextTaskNumber}`),
        },
        taskOrder: [...workspace.taskOrder, taskId],
        nextTaskNumber: workspace.nextTaskNumber + 1,
      };
    });
    if (nextTaskId.length > 0) {
      setActiveTaskIds((current) => ({
        ...current,
        [targetAgentKey]: nextTaskId,
      }));
    }
  };

  const cancelActiveRequest = async (): Promise<void> => {
    const targetAgentKey = activeAgentKey();
    if (!targetAgentKey) {
      return;
    }

    const workspace = workspaces()[targetAgentKey];
    if (!workspace) {
      return;
    }

    const targetTaskId = activeTaskIds()[targetAgentKey] ?? workspace.taskOrder[0] ?? "";
    const task = workspace.tasks[targetTaskId];
    if (!task?.activeRequestTaskId) {
      return;
    }

    const request = activeRequests.get(buildRequestKey(targetAgentKey, targetTaskId));
    if (!request || request.cancelPromise) {
      return;
    }

    request.cancelRequested = true;
    request.cancelState = "requested";
    updateTask(targetAgentKey, targetTaskId, (current) => ({
      ...current,
      isCancelling: true,
    }));

    request.cancelPromise = (async () => {
      try {
        await Promise.race([
          request.client.cancelTask(request.requestTaskId),
          new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error(CANCELLATION_TIMEOUT_MESSAGE)), CANCEL_TIMEOUT_MS);
          }),
        ]);
      } catch (error) {
        if (isTaskNotCancelableError(error)) {
          request.cancelState = "not-cancelable";
          updateTask(targetAgentKey, targetTaskId, (current) => ({
            ...current,
            isCancelling: false,
          }));
          return;
        }

        if (error instanceof Error && error.message === CANCELLATION_TIMEOUT_MESSAGE) {
          request.cancelState = "timed-out";
          request.failureMessage = CANCELLATION_TIMEOUT_MESSAGE;
          request.abortController.abort();
          return;
        }

        request.cancelState = "failed";
        request.failureMessage = error instanceof Error ? error.message : "Failed to cancel request";
        request.abortController.abort();
      }
    })();

    try {
      await request.cancelPromise;
    } finally {
      request.cancelPromise = null;
    }
  };

  const sendMessage = async (content: string): Promise<void> => {
    const targetAgentKey = activeAgentKey();
    if (!targetAgentKey) {
      throw new Error("No A2A agents available. Start a managed agent first.");
    }

    const targetWorkspace = workspaces()[targetAgentKey] ?? createWorkspace();
    const targetTaskId = activeTaskIds()[targetAgentKey] ?? targetWorkspace.taskOrder[0] ?? "task-1";
    const activeContextId =
      (targetWorkspace.tasks[targetTaskId]?.contextId ?? null) ?? buildAgentContextId(targetAgentKey);
    const requestTaskId = crypto.randomUUID();
    const requestKey = buildRequestKey(targetAgentKey, targetTaskId);

    updateTask(targetAgentKey, targetTaskId, (current) => {
      if (current.contextId) {
        return current;
      }
      return {
        ...current,
        contextId: activeContextId,
      };
    });

    const setAgentMessages: Setter<Message[]> = (value) => {
      const updated = updateTask(targetAgentKey, targetTaskId, (current) => {
        const nextMessages = typeof value === "function" ? value(current.messages) : value;
        return {
          ...current,
          messages: nextMessages,
        };
      });
      return updated.messages;
    };

    let selectedAgent = agents().find((agent) => agent.key === targetAgentKey);
    if (!selectedAgent) {
      await refreshAgents();
      selectedAgent = agents().find((agent) => agent.key === activeAgentKey());
    }

    if (!selectedAgent) {
      throw new Error("No A2A agents available. Start a managed agent first.");
    }

    const humanMessage: Message = {
      id: crypto.randomUUID(),
      type: "human",
      content,
      timestamp: timestamp(),
    };

    setAgentMessages((current) => [...current, humanMessage]);
    updateTask(targetAgentKey, targetTaskId, (current) => ({
      ...current,
      isSending: true,
      isCancelling: false,
      activeRequestTaskId: requestTaskId,
      contextId: current.contextId ?? activeContextId,
    }));

    const abortController = new AbortController();
    const a2aClient = createA2AClient({
      agentCardPath: selectedAgent.agentCardPath,
    });
    const activeRequest: ActiveChatRequest = {
      abortController,
      client: a2aClient,
      requestTaskId,
      cancelRequested: false,
      cancellationConfirmed: false,
      cancelState: "idle",
      failureMessage: null,
      cancelPromise: null,
    };
    activeRequests.set(requestKey, activeRequest);

    let activeAssistantMessageId: string | null = null;
    let activeAssistantTimestamp = "";
    let streamedAssistantText = "";
    let sawToolResult = false;
    let sawOutputAfterLastTool = false;
    let thinkingMessageId: string | null = null;
    let thinkingTimestamp = "";
    let streamedThinking = "";
    let cancellationNoticeAppended = false;
    let sawTaskIdMismatch = false;

    const beginAssistantMessage = (): void => {
      activeAssistantMessageId = crypto.randomUUID();
      activeAssistantTimestamp = timestamp();
      streamedAssistantText = "";
    };

    const ensureAssistantMessage = (): void => {
      if (activeAssistantMessageId !== null) {
        return;
      }
      beginAssistantMessage();
    };

    const clearAssistantMessage = (): void => {
      activeAssistantMessageId = null;
      activeAssistantTimestamp = "";
      streamedAssistantText = "";
    };

    const removeAssistantMessage = (): void => {
      if (activeAssistantMessageId === null) {
        return;
      }
      const targetMessageId = activeAssistantMessageId;
      setAgentMessages((current) => current.filter((message) => message.id !== targetMessageId));
      clearAssistantMessage();
    };

    const appendAssistantChunk = (chunk: string): void => {
      if (chunk.length === 0) {
        return;
      }

      ensureAssistantMessage();
      streamedAssistantText = `${streamedAssistantText}${chunk}`;
      upsertAIMessage(
        setAgentMessages,
        activeAssistantMessageId!,
        streamedAssistantText,
        activeAssistantTimestamp,
      );
    };

    const setAssistantText = (text: string): void => {
      ensureAssistantMessage();
      streamedAssistantText = text;
      upsertAIMessage(
        setAgentMessages,
        activeAssistantMessageId!,
        streamedAssistantText,
        activeAssistantTimestamp,
      );
    };

    const appendThinkingChunk = (chunk: string): void => {
      if (chunk.length === 0) {
        return;
      }

      if (thinkingMessageId === null) {
        thinkingMessageId = crypto.randomUUID();
        thinkingTimestamp = timestamp();
      }

      streamedThinking = `${streamedThinking}${chunk}`;
      upsertThinkingMessage(setAgentMessages, thinkingMessageId, streamedThinking, thinkingTimestamp);
    };

    const setThinkingText = (text: string): void => {
      if (thinkingMessageId === null) {
        thinkingMessageId = crypto.randomUUID();
        thinkingTimestamp = timestamp();
      }

      streamedThinking = text;
      upsertThinkingMessage(setAgentMessages, thinkingMessageId, streamedThinking, thinkingTimestamp);
    };

    const startNewThinkingBlock = (): void => {
      thinkingMessageId = crypto.randomUUID();
      thinkingTimestamp = timestamp();
      streamedThinking = "";
    };

    const finishThinkingBlock = (): void => {
      thinkingMessageId = null;
      thinkingTimestamp = "";
      streamedThinking = "";
    };

    const appendToolNotice = (
      contentValue: string,
      status: Message["toolStatus"],
      toolName: string = "A2A",
    ): void => {
      setAgentMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          type: "tool",
          toolName,
          content: contentValue,
          toolStatus: status,
          timestamp: timestamp(),
        },
      ]);
    };

    try {
      await a2aClient.sendMessageStream(
        createTextMessageParams(content, activeContextId, requestTaskId),
        (event) => {
          const eventTaskId = readEventTaskId(event);
          if (eventTaskId && eventTaskId !== requestTaskId) {
            sawTaskIdMismatch = true;
            activeRequest.failureMessage =
              `Received mismatched task id '${eventTaskId}' while streaming '${requestTaskId}'.`;
            activeRequest.abortController.abort();
            return;
          }

          const taskState = readEventStatusState(event);
          if (taskState === "canceled") {
            finishThinkingBlock();
            activeRequest.cancellationConfirmed = true;
            if (!cancellationNoticeAppended) {
              appendToolNotice("Request canceled.", "cancelled");
              cancellationNoticeAppended = true;
            }
            return;
          }

          if (event.kind === "message") {
            return;
          }

          if (event.kind === "status-update" || event.kind === "task") {
            return;
          }

          if (event.kind === "artifact-update") {
            const payload = event as { artifact?: { name?: unknown; parts?: unknown } };
            const artifactName = typeof payload.artifact?.name === "string" ? payload.artifact.name : "Artifact";
            const artifactText = readTextParts(payload.artifact?.parts);

            if (artifactName === "output_start" || artifactName === "output_delta") {
              if (sawToolResult) {
                sawOutputAfterLastTool = true;
              }
              appendAssistantChunk(artifactText);
              return;
            }

            if (artifactName === "output_end" || artifactName === "full_output") {
              if (artifactText.length > 0) {
                if (artifactName === "full_output") {
                  if (sawToolResult && !sawOutputAfterLastTool) {
                    clearAssistantMessage();
                  }
                }
                if (sawToolResult) {
                  sawOutputAfterLastTool = true;
                }
                setAssistantText(artifactText);
              }
              return;
            }

            if (artifactName === "thinking_start") {
              startNewThinkingBlock();
              appendThinkingChunk(artifactText);
              return;
            }

            if (artifactName === "thinking_delta") {
              appendThinkingChunk(artifactText);
              return;
            }

            if (artifactName === "thinking_end") {
              if (artifactText.length > 0) {
                setThinkingText(artifactText);
              }
              finishThinkingBlock();
              return;
            }

            if (artifactName === "tool_result") {
              finishThinkingBlock();

              if (!sawToolResult && activeAssistantMessageId !== null) {
                removeAssistantMessage();
              }
              sawToolResult = true;
              sawOutputAfterLastTool = false;
              clearAssistantMessage();

              const dataParts = readDataParts(payload.artifact?.parts);
              const firstDataPart = dataParts[0];
              const toolNameFromData = firstDataPart?.toolName;
              const toolName = typeof toolNameFromData === "string" ? toolNameFromData : artifactName;
              const toolCallId = typeof firstDataPart?.toolCallId === "string" ? firstDataPart.toolCallId : undefined;
              const toolCallParamsText = toPrettyText(firstDataPart?.args);
              const toolResultText = firstDataPart ? toPrettyText(firstDataPart.result) : artifactText;
              const okFromData = firstDataPart?.ok;
              const toolStatus = okFromData === false ? "error" : "success";

              const toolCallMessage: Message = {
                id: crypto.randomUUID(),
                type: "tool-call",
                content: toolResultText,
                toolName,
                toolCallId,
                toolCallArgs: firstDataPart?.args,
                toolResultData: firstDataPart?.result,
                toolCallParams: toolCallParamsText,
                toolResult: toolResultText,
                toolStatus,
                timestamp: timestamp(),
              };

              setAgentMessages((current) => [...current, toolCallMessage]);
              return;
            }

            if (artifactName === "tool_call") {
              finishThinkingBlock();
              return;
            }

            const toolMessage: Message = {
              id: crypto.randomUUID(),
              type: "tool",
              toolName: artifactName,
              content: artifactText || "Artifact received",
              toolStatus: "success",
              timestamp: timestamp(),
            };

            setAgentMessages((current) => [...current, toolMessage]);
          }
        },
        abortController.signal,
      );

      finishThinkingBlock();
    } catch (error) {
      finishThinkingBlock();

      if (activeRequest.cancellationConfirmed) {
        if (!cancellationNoticeAppended) {
          appendToolNotice("Request canceled.", "cancelled");
        }
        return;
      }

      if (activeRequest.cancelState === "timed-out" || activeRequest.cancelState === "failed") {
        appendToolNotice(activeRequest.failureMessage ?? "Failed to cancel request", "error");
        return;
      }

      if (sawTaskIdMismatch) {
        appendToolNotice(activeRequest.failureMessage ?? "Received mismatched task id during streaming.", "error");
        throw error;
      }

      if (activeRequest.cancelRequested && isAbortError(error)) {
        return;
      }

      appendToolNotice(error instanceof Error ? error.message : "Failed to send message", "error");
      throw error;
    } finally {
      updateTask(targetAgentKey, targetTaskId, (current) => ({
        ...current,
        isSending: false,
        isCancelling: false,
        activeRequestTaskId: current.activeRequestTaskId === requestTaskId ? null : current.activeRequestTaskId,
      }));
      activeRequests.delete(requestKey);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        sendMessage,
        cancelActiveRequest,
        isSending,
        isCancelling,
        tasks,
        activeTaskId,
        setActiveTaskId,
        createTask,
      }}
    >
      {props.children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);

  if (!context) {
    throw new Error("useChat must be used within ChatProvider");
  }

  return context;
}
