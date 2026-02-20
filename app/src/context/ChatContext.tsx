import type { MessageSendParams } from "@a2a-js/sdk";
import {
  createContext,
  createSignal,
  onMount,
  useContext,
  type Accessor,
  type JSX,
  type Setter,
} from "solid-js";
import { createA2AClient, DEFAULT_A2A_BASE_URL } from "~/a2a/client";
import type { Message } from "~/data/sampleMessages";

export interface AgentEndpoint {
  key: string;
  name: string;
  mountPath: string;
  agentCardPath: string;
  url: string;
}

interface ChatContextValue {
  messages: Accessor<Message[]>;
  setMessages: Setter<Message[]>;
  sendMessage: (content: string) => Promise<void>;
  isSending: Accessor<boolean>;
  agents: Accessor<AgentEndpoint[]>;
  activeAgentKey: Accessor<string>;
  activeAgentName: Accessor<string>;
  setActiveAgentKey: (agentKey: string) => void;
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

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
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

function appendMessageKeepingAssistantLast(
  current: Message[],
  messageToAppend: Message,
  assistantMessageId: string,
): Message[] {
  const next = [...current, messageToAppend];
  const assistantIndex = next.findIndex((message) => message.id === assistantMessageId);

  if (assistantIndex === -1 || assistantIndex === next.length - 1) {
    return next;
  }

  const assistantMessage = next[assistantIndex];
  const withoutAssistant = next.filter((_, index) => index !== assistantIndex);
  return [...withoutAssistant, assistantMessage];
}

export function ChatProvider(props: { children: JSX.Element; messages: Message[] }) {
  const [messages, setMessages] = createSignal(props.messages || []);
  const [isSending, setIsSending] = createSignal(false);
  const [agents, setAgents] = createSignal<AgentEndpoint[]>([]);
  const [activeAgentKey, setActiveAgentKeySignal] = createSignal("buddy");
  const [activeAgentName, setActiveAgentName] = createSignal("buddy");
  const [conversationContextId, setConversationContextId] = createSignal<string | null>(null);

  onMount(async () => {
    try {
      const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents`);
      if (!response.ok) {
        return;
      }

      const payload = (await response.json()) as {
        defaultAgentKey?: unknown;
        agents?: unknown;
      };

      if (!Array.isArray(payload.agents)) {
        return;
      }

      const loadedAgents = payload.agents
        .map((entry) => {
          if (!entry || typeof entry !== "object") {
            return null;
          }

          const candidate = entry as {
            key?: unknown;
            name?: unknown;
            mountPath?: unknown;
            agentCardPath?: unknown;
            url?: unknown;
          };

          if (
            typeof candidate.key !== "string" ||
            typeof candidate.name !== "string" ||
            typeof candidate.mountPath !== "string" ||
            typeof candidate.agentCardPath !== "string" ||
            typeof candidate.url !== "string"
          ) {
            return null;
          }

          return {
            key: candidate.key,
            name: candidate.name,
            mountPath: candidate.mountPath,
            agentCardPath: candidate.agentCardPath,
            url: candidate.url,
          } as AgentEndpoint;
        })
        .filter((entry): entry is AgentEndpoint => entry !== null);

      if (loadedAgents.length === 0) {
        return;
      }

      setAgents(loadedAgents);

      const defaultAgentKey =
        typeof payload.defaultAgentKey === "string" &&
        loadedAgents.some((agent) => agent.key === payload.defaultAgentKey)
          ? payload.defaultAgentKey
          : loadedAgents[0].key;

      const defaultAgent = loadedAgents.find((agent) => agent.key === defaultAgentKey) ?? loadedAgents[0];
      setActiveAgentKeySignal(defaultAgent.key);
      setActiveAgentName(defaultAgent.name);
    } catch {
      setAgents([
        {
          key: "buddy",
          name: "buddy-agent",
          mountPath: "/a2a/buddy",
          agentCardPath: "/a2a/buddy/.well-known/agent-card.json",
          url: "/a2a/buddy",
        },
      ]);
      setActiveAgentKeySignal("buddy");
      setActiveAgentName("buddy-agent");
    }
  });

  const setActiveAgentKey = (agentKey: string): void => {
    const selectedAgent = agents().find((agent) => agent.key === agentKey);
    if (!selectedAgent) {
      return;
    }
    setActiveAgentKeySignal(selectedAgent.key);
    setActiveAgentName(selectedAgent.name);
  };

  const sendMessage = async (content: string): Promise<void> => {
    const activeContextId = conversationContextId() ?? crypto.randomUUID();
    if (conversationContextId() === null) {
      setConversationContextId(activeContextId);
    }

    const humanMessage: Message = {
      id: crypto.randomUUID(),
      type: "human",
      content,
      timestamp: timestamp(),
    };

    setMessages((current) => [...current, humanMessage]);
    setIsSending(true);

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
      upsertAIMessage(setMessages, assistantMessageId, streamedText, assistantTimestamp);
    };

    const setAssistantText = (text: string): void => {
      streamedText = text;
      upsertAIMessage(setMessages, assistantMessageId, streamedText, assistantTimestamp);
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
      upsertThinkingMessage(setMessages, thinkingMessageId, streamedThinking, thinkingTimestamp);
    };

    const setThinkingText = (text: string): void => {
      if (thinkingMessageId === null) {
        thinkingMessageId = crypto.randomUUID();
        thinkingTimestamp = timestamp();
      }

      streamedThinking = text;
      upsertThinkingMessage(setMessages, thinkingMessageId, streamedThinking, thinkingTimestamp);
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
      const selectedAgent = agents().find((agent) => agent.key === activeAgentKey());
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

            setMessages((current) =>
              appendMessageKeepingAssistantLast(current, toolCallMessage, assistantMessageId),
            );
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

          setMessages((current) =>
            appendMessageKeepingAssistantLast(current, toolMessage, assistantMessageId),
          );
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

      setMessages((current) => [...current, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        setMessages,
        sendMessage,
        isSending,
        agents,
        activeAgentKey,
        activeAgentName,
        setActiveAgentKey,
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
