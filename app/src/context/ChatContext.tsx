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
import { createA2AClient } from "~/a2a/client";
import {
  CANCELLATION_TIMEOUT_MESSAGE,
  CANCEL_TIMEOUT_MS,
  createTextMessageParams,
  isAbortError,
  isTaskNotCancelableError,
  readDataParts,
  readEventStatusState,
  readEventTaskId,
  readTextParts,
  toPrettyText,
} from "~/context/chatEvents";
import {
  buildAgentContextId,
  buildRequestKey,
  createWorkspace,
  emptyConversation,
  timestamp,
  type ActiveChatRequest,
  type AgentConversationState,
  type AgentWorkspaceState,
  upsertAIMessage,
  upsertThinkingMessage,
} from "~/context/chatState";
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

export function ChatProvider(props: { children: JSX.Element; messages: Message[] }) {
  const { agents, activeAgentKey, refreshAgents } = useAgents();
  const [workspaces, setWorkspaces] = createSignal<Record<string, AgentWorkspaceState>>({});
  const [activeTaskIds, setActiveTaskIds] = createSignal<Record<string, string>>({});
  const activeRequests = new Map<string, ActiveChatRequest>();

  const readWorkspace = (agentKey: string): AgentWorkspaceState | null => workspaces()[agentKey] ?? null;
  const readSelectedTaskId = (agentKey: string, workspace: AgentWorkspaceState | null): string =>
    workspace ? activeTaskIds()[agentKey] ?? workspace.taskOrder[0] ?? "" : "";

  const messages = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = readWorkspace(activeKey);
    const selectedTaskId = readSelectedTaskId(activeKey, workspace);
    return workspace?.tasks[selectedTaskId]?.messages ?? [];
  });

  const isSending = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = readWorkspace(activeKey);
    const selectedTaskId = readSelectedTaskId(activeKey, workspace);
    return workspace?.tasks[selectedTaskId]?.isSending ?? false;
  });

  const isCancelling = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = readWorkspace(activeKey);
    const selectedTaskId = readSelectedTaskId(activeKey, workspace);
    return workspace?.tasks[selectedTaskId]?.isCancelling ?? false;
  });

  const activeTaskId = createMemo(() => {
    const activeKey = activeAgentKey();
    return readSelectedTaskId(activeKey, readWorkspace(activeKey));
  });

  const tasks = createMemo(() => {
    const activeKey = activeAgentKey();
    const workspace = readWorkspace(activeKey);
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
    const workspace = readWorkspace(targetAgentKey);
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

    const workspace = readWorkspace(targetAgentKey);
    if (!workspace) {
      return;
    }

    const targetTaskId = readSelectedTaskId(targetAgentKey, workspace);
    const task = workspace.tasks[targetTaskId];
    if (!task?.isSending) {
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
        if (!request.requestTaskId) {
          request.cancellationConfirmed = true;
          request.abortController.abort();
          return;
        }

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

    const targetWorkspace = readWorkspace(targetAgentKey) ?? createWorkspace();
    const targetTaskId = readSelectedTaskId(targetAgentKey, targetWorkspace) || "task-1";
    const activeContextId =
      (targetWorkspace.tasks[targetTaskId]?.contextId ?? null) ?? buildAgentContextId(targetAgentKey);
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
      activeRequestTaskId: null,
      contextId: current.contextId ?? activeContextId,
    }));

    const abortController = new AbortController();
    const a2aClient = createA2AClient({
      agentCardPath: selectedAgent.agentCardPath,
    });
    const activeRequest: ActiveChatRequest = {
      abortController,
      client: a2aClient,
      requestTaskId: null,
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
        createTextMessageParams(content, activeContextId),
        (event) => {
          const eventTaskId = readEventTaskId(event);
          if (eventTaskId) {
            if (activeRequest.requestTaskId === null) {
              activeRequest.requestTaskId = eventTaskId;
              updateTask(targetAgentKey, targetTaskId, (current) => ({
                ...current,
                activeRequestTaskId: eventTaskId,
              }));
            } else if (eventTaskId !== activeRequest.requestTaskId) {
              sawTaskIdMismatch = true;
              activeRequest.failureMessage =
                `Received mismatched task id '${eventTaskId}' while streaming '${activeRequest.requestTaskId}'.`;
              activeRequest.abortController.abort();
              return;
            }
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
        activeRequestTaskId: null,
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
