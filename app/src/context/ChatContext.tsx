import type { MessageSendParams } from "@a2a-js/sdk";
import { useQuery, useQueryClient } from "@tanstack/solid-query";
import {
  createEffect,
  createContext,
  createMemo,
  createSignal,
  useContext,
  type Accessor,
  type JSX,
  type Setter,
} from "solid-js";
import { readJson } from "~/a2a/http";
import {
  AgentCardSchema,
  AgentsIndexResponseSchema,
  type AgentCardPayload,
} from "~/a2a/schemas";
import { createA2AClient, DEFAULT_A2A_BASE_URL } from "~/a2a/client";
import type { Message } from "~/data/sampleMessages";

export interface AgentEndpoint {
  key: string;
  name: string;
  mountPath: string;
  agentCardPath: string;
  url: string;
  description: string | null;
  version: string | null;
  skills: string[];
}

interface ChatContextValue {
  messages: Accessor<Message[]>;
  sendMessage: (content: string) => Promise<void>;
  isSending: Accessor<boolean>;
  refreshAgents: () => Promise<void>;
  agents: Accessor<AgentEndpoint[]>;
  activeAgentKey: Accessor<string>;
  activeAgentName: Accessor<string>;
  setActiveAgentKey: (agentKey: string) => void;
  tasks: Accessor<{ id: string; label: string; isSending: boolean }[]>;
  activeTaskId: Accessor<string>;
  setActiveTaskId: (taskId: string) => void;
  createTask: () => void;
}

const ChatContext = createContext<ChatContextValue>();

function createTextMessageParams(text: string, contextId: string): MessageSendParams {
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

interface AgentCardDetails {
  description: string | null;
  version: string | null;
  skills: string[];
}

interface AgentConversationState {
  messages: Message[];
  isSending: boolean;
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
    contextId: null,
    label,
  };
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

function toNormalizedString(value: string | null | undefined): string | null {
  if (typeof value !== "string") {
    return null;
  }

  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
}

function toAgentCardDetails(payload: AgentCardPayload): AgentCardDetails {
  const skills = (payload.skills ?? [])
    .map((skill) => toNormalizedString(skill.name) ?? toNormalizedString(skill.id))
    .filter((entry): entry is string => entry !== null);

  return {
    description: toNormalizedString(payload.description),
    version: toNormalizedString(payload.version),
    skills,
  };
}

function resolveAgentCardUrl(agentCardPath: string): string {
  if (agentCardPath.startsWith("http://") || agentCardPath.startsWith("https://")) {
    return agentCardPath;
  }

  if (agentCardPath.startsWith("/")) {
    return `${DEFAULT_A2A_BASE_URL}${agentCardPath}`;
  }

  return `${DEFAULT_A2A_BASE_URL}/${agentCardPath}`;
}

interface AgentsIndexPayload {
  defaultAgentKey: string | null;
  agents: AgentEndpoint[];
}

async function fetchWithTimeout(input: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function fetchAgentsIndex(): Promise<AgentsIndexPayload> {
  const response = await fetchWithTimeout(`${DEFAULT_A2A_BASE_URL}/agents`, { cache: "no-store" }, 5000);
  const payload = await readJson(response, AgentsIndexResponseSchema);

  const agents = payload.agents.map((entry) => ({
    key: entry.key,
    name: entry.name,
    mountPath: entry.mountPath,
    agentCardPath: entry.agentCardPath,
    url: entry.url,
    description: null,
    version: null,
    skills: [],
  }));

  if (agents.length === 0) {
    throw new Error("No agents returned from /agents");
  }

  const defaultAgentKey =
    typeof payload.defaultAgentKey === "string" && agents.some((agent) => agent.key === payload.defaultAgentKey)
      ? payload.defaultAgentKey
      : null;

  return {
    defaultAgentKey,
    agents,
  };
}

async function fetchAgentCardDetails(agentCardPath: string): Promise<AgentCardDetails> {
  const cardResponse = await fetchWithTimeout(resolveAgentCardUrl(agentCardPath), { cache: "no-store" }, 4000);
  try {
    const cardPayload = await readJson(cardResponse, AgentCardSchema);
    return toAgentCardDetails(cardPayload);
  } catch {
    return {
      description: null,
      version: null,
      skills: [],
    };
  }
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
  let refreshRequestId = 0;
  const [workspaces, setWorkspaces] = createSignal<Record<string, AgentWorkspaceState>>({
    buddy: createWorkspace(props.messages || []),
  });
  const [activeTaskIds, setActiveTaskIds] = createSignal<Record<string, string>>({
    buddy: "task-1",
  });
  const [agents, setAgents] = createSignal<AgentEndpoint[]>([]);
  const [activeAgentKey, setActiveAgentKeySignal] = createSignal("buddy");
  const [activeAgentName, setActiveAgentName] = createSignal("buddy");

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

  const queryClient = useQueryClient();
  const agentsIndexQuery = useQuery(() => ({
    queryKey: ["agents", "index"],
    queryFn: fetchAgentsIndex,
    enabled: false,
  }));

  const refreshAgents = async (): Promise<void> => {
    await queryClient.invalidateQueries({ queryKey: ["agents"] });
    const result = await agentsIndexQuery.refetch();
    if (result.error) {
      throw result.error;
    }
  };

  createEffect(() => {
    const payload = agentsIndexQuery.data;
    if (!payload) {
      return;
    }

    const requestId = ++refreshRequestId;
    const loadedAgents = payload.agents;

    setAgents(loadedAgents);

    const currentActiveKey = activeAgentKey();
    const fallbackAgentKey =
      typeof payload.defaultAgentKey === "string" && loadedAgents.some((agent) => agent.key === payload.defaultAgentKey)
        ? payload.defaultAgentKey
        : loadedAgents[0].key;
    const nextActiveKey = loadedAgents.some((agent) => agent.key === currentActiveKey)
      ? currentActiveKey
      : fallbackAgentKey;
    const nextActiveAgent =
      loadedAgents.find((agent) => agent.key === nextActiveKey) ?? loadedAgents[0];
    setActiveAgentKeySignal(nextActiveAgent.key);
    setActiveAgentName(nextActiveAgent.name);

    setWorkspaces((current) => {
      const next = { ...current };
      for (const agent of loadedAgents) {
        if (!next[agent.key]) {
          next[agent.key] = createWorkspace();
        }
      }
      return next;
    });

    setActiveTaskIds((current) => {
      const next = { ...current };
      for (const agent of loadedAgents) {
        if (!next[agent.key]) {
          next[agent.key] = "task-1";
        }
      }
      return next;
    });

    void (async () => {
      const loadedAgentsWithDetails = await Promise.all(
        loadedAgents.map(async (agent) => {
          try {
            const details = await queryClient.fetchQuery({
              queryKey: ["agents", "card", agent.agentCardPath],
              queryFn: () => fetchAgentCardDetails(agent.agentCardPath),
            });
            return {
              ...agent,
              description: details.description,
              version: details.version,
              skills: details.skills,
            };
          } catch {
            return agent;
          }
        }),
      );

      if (requestId !== refreshRequestId) {
        return;
      }

      setAgents(loadedAgentsWithDetails);
    })();
  });

  const setActiveAgentKey = (agentKey: string): void => {
    const selectedAgent = agents().find((agent) => agent.key === agentKey);
    if (!selectedAgent) {
      return;
    }
    setWorkspaces((current) => {
      if (current[selectedAgent.key]) {
        return current;
      }

      return {
        ...current,
        [selectedAgent.key]: createWorkspace(),
      };
    });
    setActiveTaskIds((current) => {
      if (current[selectedAgent.key]) {
        return current;
      }
      return {
        ...current,
        [selectedAgent.key]: "task-1",
      };
    });
    setActiveAgentKeySignal(selectedAgent.key);
    setActiveAgentName(selectedAgent.name);
  };

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

  const sendMessage = async (content: string): Promise<void> => {
    const targetAgentKey = activeAgentKey();
    const targetWorkspace = workspaces()[targetAgentKey] ?? createWorkspace();
    const targetTaskId = activeTaskIds()[targetAgentKey] ?? targetWorkspace.taskOrder[0] ?? "task-1";
    const activeContextId =
      (targetWorkspace.tasks[targetTaskId]?.contextId ?? null) ?? buildAgentContextId(targetAgentKey);

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
      contextId: current.contextId ?? activeContextId,
    }));

    const assistantMessageId = crypto.randomUUID();
    const assistantTimestamp = timestamp();
    let streamedText = "";
    let thinkingMessageId: string | null = null;
    let thinkingTimestamp = "";
    let streamedThinking = "";

    const appendAssistantChunk = (chunk: string): void => {
      if (chunk.length === 0) {
        return;
      }

      streamedText = `${streamedText}${chunk}`;
      upsertAIMessage(setAgentMessages, assistantMessageId, streamedText, assistantTimestamp);
    };

    const setAssistantText = (text: string): void => {
      streamedText = text;
      upsertAIMessage(setAgentMessages, assistantMessageId, streamedText, assistantTimestamp);
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

    try {
      const selectedAgent = agents().find((agent) => agent.key === targetAgentKey);
      const agentCardPath = selectedAgent?.agentCardPath ?? "/a2a/buddy/.well-known/agent-card.json";
      const a2aClient = createA2AClient({
        agentCardPath,
      });

      await a2aClient.sendMessageStream(createTextMessageParams(content, activeContextId), (event) => {
        if (event.kind === "message") {
          const payload = event as { role?: unknown; parts?: unknown };
          const isAgentMessage = payload.role === "agent";
          const text = readTextParts(payload.parts);

          if (isAgentMessage && text.length > 0) {
            setAssistantText(text);
          }
          return;
        }

        if (event.kind === "status-update") {
          return;
        }

        if (event.kind === "artifact-update") {
          const payload = event as { artifact?: { name?: unknown; parts?: unknown } };
          const artifactName = typeof payload.artifact?.name === "string" ? payload.artifact.name : "Artifact";
          const artifactText = readTextParts(payload.artifact?.parts);

          if (artifactName === "output_start" || artifactName === "output_delta") {
            appendAssistantChunk(artifactText);
            return;
          }

          if (artifactName === "output_end" || artifactName === "full_output") {
            if (artifactText.length > 0) {
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
      });

      finishThinkingBlock();

      if (streamedText.length === 0) {
        setAssistantText("");
      }
    } catch (error) {
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        type: "tool",
        toolName: "A2A",
        content: error instanceof Error ? error.message : "Failed to send message",
        toolStatus: "error",
        timestamp: timestamp(),
      };

      setAgentMessages((current) => [...current, errorMessage]);
      throw error;
    } finally {
      updateTask(targetAgentKey, targetTaskId, (current) => ({
        ...current,
        isSending: false,
      }));
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        sendMessage,
        isSending,
        refreshAgents,
        agents,
        activeAgentKey,
        activeAgentName,
        setActiveAgentKey,
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
