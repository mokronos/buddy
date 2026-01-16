import { A2AClient } from "@a2a-js/sdk/client";
import type {
  AgentCard,
  Message,
  MessageSendParams,
  Part,
  Task,
  TaskArtifactUpdateEvent,
  TaskStatusUpdateEvent,
} from "@a2a-js/sdk";

export type SessionSummary = {
  sessionId: string;
  createdAt: string;
  updatedAt: string;
};

type SessionSummaryWire = {
  session_id: string;
  created_at: string;
  updated_at: string;
};

type SessionRestorePayloadWire = {
  session: SessionSummaryWire;
  messages: { id: string; role: "user" | "assistant" | "status"; content: string }[];
  events: StreamEvent[];
};

export type SessionRestorePayload = {
  session: SessionSummary;
  messages: { id: string; role: "user" | "assistant" | "status"; content: string }[];
  events: StreamEvent[];
};

export type StreamEvent = Message | Task | TaskArtifactUpdateEvent | TaskStatusUpdateEvent;

export const createA2AClient = (baseUrl: string) => new A2AClient(baseUrl);

export const buildUserMessage = (
  text: string,
  contextId?: string,
  taskId?: string,
): Message => {
  const message: Message = {
    messageId: crypto.randomUUID(),
    kind: "message",
    role: "user",
    parts: [{ kind: "text", text }],
  };

  if (contextId) {
    message.contextId = contextId;
  }
  if (taskId) {
    message.taskId = taskId;
  }

  return message;
};

export const streamMessage = async (
  client: A2AClient,
  message: Message,
  onEvent: (event: StreamEvent) => void,
) => {
  const params: MessageSendParams = {
    message,
  };

  const stream = client.sendMessageStream(params);
  for await (const event of stream) {
    onEvent(event as StreamEvent);
  }
};

export const fetchSessions = async (baseUrl: string, limit = 20): Promise<SessionSummary[]> => {
  const response = await fetch(`${baseUrl}/sessions?limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to fetch sessions");
  }
  const data = (await response.json()) as { sessions: SessionSummaryWire[] };
  return (data.sessions ?? []).map((session) => ({
    sessionId: session.session_id,
    createdAt: session.created_at,
    updatedAt: session.updated_at,
  }));
};

export const fetchSession = async (baseUrl: string, sessionId: string): Promise<SessionRestorePayload> => {
  const response = await fetch(`${baseUrl}/sessions/${sessionId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch session");
  }
  const data = (await response.json()) as SessionRestorePayloadWire;
  return {
    session: {
      sessionId: data.session.session_id,
      createdAt: data.session.created_at,
      updatedAt: data.session.updated_at,
    },
    messages: data.messages ?? [],
    events: data.events ?? [],
  };
};

export const getTextFromParts = (parts: Part[]) => {
  if (!parts) {
    return "";
  }
  return parts
    .filter((part) => part.kind === "text")
    .map((part) => part.text ?? "")
    .join("");
};

export const getTextFromMessage = (message: Message) => getTextFromParts(message.parts ?? []);

export type { AgentCard };
