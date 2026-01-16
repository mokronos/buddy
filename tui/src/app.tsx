import { useEffect, useMemo, useRef, useState } from "react";
import type { InputRenderable, SelectOption } from "@opentui/core";
import { useKeyboard } from "@opentui/react";

import { ChatPanel, type ChatMessage } from "./components/chat-panel";
import { StatusPanel } from "./components/status-panel";
import {
  buildUserMessage,
  createA2AClient,
  fetchSession,
  fetchSessions,
  getTextFromMessage,
  getTextFromParts,
  streamMessage,
  type SessionSummary,
  type StreamEvent,
} from "./lib/a2a-client";
import { fetchAgentCard } from "./lib/server-status";

const DEFAULT_SERVER_URL = process.env.TUI_SERVER_URL ?? "http://localhost:10001";

export const App = () => {
  const [serverUrl] = useState(DEFAULT_SERVER_URL);
  const [agentName, setAgentName] = useState("Unknown Agent");
  const [connected, setConnected] = useState(false);
  const [statusText, setStatusText] = useState("Disconnected");
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [, setInputValue] = useState("");
  const [inputKey, setInputKey] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [taskId, setTaskId] = useState<string | undefined>(undefined);
  const [contextId, setContextId] = useState<string | undefined>(undefined);
  const [sessionList, setSessionList] = useState<SessionSummary[]>([]);
  const [showSessionPicker, setShowSessionPicker] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

  const clientRef = useRef<ReturnType<typeof createA2AClient> | null>(null);
  const inputRef = useRef<InputRenderable | null>(null);
  const assistantMessageIdRef = useRef<string | null>(null);
  const streamingOutputRef = useRef(false);
  const finalOutputRenderedRef = useRef(false);

  useKeyboard((key) => {
    if (showSessionPicker && key.name === "escape") {
      setShowSessionPicker(false);
      setTimeout(() => inputRef.current?.focus(), 0);
      return;
    }

    if (showSessionPicker) {
      return;
    }

    if (key.ctrl && key.name === "w") {
      const input = inputRef.current;
      if (!input) {
        return;
      }

      const value = input.value ?? "";
      const cursor = input.cursorPosition ?? value.length;
      const beforeCursor = value.slice(0, cursor);
      const afterCursor = value.slice(cursor);
      const trimmed = beforeCursor.replace(/\s+$/, "");
      const newBefore = trimmed.replace(/\S+$/, "");
      const newValue = newBefore + afterCursor;
      const newCursor = newBefore.length;

      if (newValue !== value) {
        input.value = newValue;
        input.cursorPosition = newCursor;
      }
    }
  });

  const connectToServer = async () => {
    const client = createA2AClient(serverUrl);
    clientRef.current = client;
    setStatusText("Connecting...");

    try {
      const card = await fetchAgentCard(client);
      setAgentName(card.name ?? "Agent");
      setConnected(true);
      setError(null);
      setStatusText("Connected");
    } catch (err) {
      setConnected(false);
      setError(err instanceof Error ? err.message : "Failed to connect");
      setStatusText("Disconnected");
    }
  };

  const loadSessions = async () => {
    try {
      const sessions = await fetchSessions(serverUrl);
      setSessionList(sessions);
      setSessionError(null);
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to load sessions");
    }
  };

  useEffect(() => {
    void connectToServer();

    return () => {
      clientRef.current = null;
    };
  }, [serverUrl]);

  useEffect(() => {
    if (showSessionPicker) {
      void loadSessions();
    }
  }, [showSessionPicker]);

  const appendMessage = (message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  };

  const updateMessage = (id: string, updater: (message: ChatMessage) => ChatMessage) => {
    setMessages((prev) => prev.map((message) => (message.id === id ? updater(message) : message)));
  };

  const ensureAssistantMessage = (content: string) => {
    if (!assistantMessageIdRef.current) {
      const id = crypto.randomUUID();
      assistantMessageIdRef.current = id;
      appendMessage({ id, role: "assistant", content, streaming: true });
      return id;
    }

    updateMessage(assistantMessageIdRef.current, (message) => ({
      ...message,
      content: message.content + content,
      streaming: true,
    }));

    return assistantMessageIdRef.current;
  };

  const finalizeStreamingMessage = (content?: string) => {
    if (!assistantMessageIdRef.current) {
      return;
    }

    updateMessage(assistantMessageIdRef.current, (message) => ({
      ...message,
      content: content ?? message.content,
      streaming: false,
    }));
    assistantMessageIdRef.current = null;
    streamingOutputRef.current = false;
  };

  const handleEvent = (event: StreamEvent) => {
    if (!event || typeof event !== "object" || !("kind" in event)) {
      return;
    }

    if (event.kind === "message") {
      if (event.taskId) {
        setTaskId(event.taskId);
      }
      if (event.contextId) {
        setContextId(event.contextId);
      }
      return;
    }

    if (event.kind === "status-update") {
      const stateText = event.status.state ?? "unknown";
      setStatusText(stateText);
      if (event.taskId) {
        setTaskId(event.taskId);
      }
      if (event.contextId) {
        setContextId(event.contextId);
      }
      if (event.status.message) {
        const statusMessage = getTextFromMessage(event.status.message);
        if (statusMessage) {
          appendMessage({
            id: crypto.randomUUID(),
            role: "status",
            content: statusMessage,
          });
        }
      }
      if (event.final && event.status.state !== "input-required") {
        setTaskId(undefined);
        finalizeStreamingMessage();
      }
      return;
    }

    if (event.kind === "artifact-update") {
      const artifactName = event.artifact.name ?? "";
      const text = getTextFromParts(event.artifact.parts);
      if (!text) {
        return;
      }

      if (artifactName === "output_start") {
        return;
      }

      if (artifactName === "output_delta") {
        streamingOutputRef.current = true;
        ensureAssistantMessage(text);
        return;
      }

      if (artifactName === "output_end" || artifactName === "full_output") {
        if (streamingOutputRef.current) {
          if (assistantMessageIdRef.current) {
            finalizeStreamingMessage(text);
          } else {
            appendMessage({ id: crypto.randomUUID(), role: "assistant", content: text });
          }
          finalOutputRenderedRef.current = true;
          return;
        }

        if (finalOutputRenderedRef.current) {
          return;
        }

        finalOutputRenderedRef.current = true;
        appendMessage({ id: crypto.randomUUID(), role: "assistant", content: text });
        return;
      }

      appendMessage({ id: crypto.randomUUID(), role: "assistant", content: text });
      return;
    }

    if (event.kind === "task") {
      if (event.id) {
        setTaskId(event.id);
      }
      if (event.contextId) {
        setContextId(event.contextId);
      }
      if (event.status?.message) {
        const statusMessage = getTextFromMessage(event.status.message);
        if (statusMessage) {
          appendMessage({ id: crypto.randomUUID(), role: "status", content: statusMessage });
        }
      }
    }
  };

  const handleSend = async (value: string) => {
    const client = clientRef.current;
    const trimmed = value.trim();
    if (!trimmed) {
      return;
    }

    if (trimmed === "/connect") {
      setInputValue("");
      setInputKey((prev) => prev + 1);
      await connectToServer();
      return;
    }

    if (trimmed === "/sessions") {
      setInputValue("");
      setInputKey((prev) => prev + 1);
      setSelectedSessionIndex(0);
      setShowSessionPicker(true);
      return;
    }

    if (!client) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    appendMessage(userMessage);
    setInputValue("");
    setInputKey((prev) => prev + 1);
    setIsSending(true);
    setError(null);
    streamingOutputRef.current = false;
    finalOutputRenderedRef.current = false;
    assistantMessageIdRef.current = null;

    const message = buildUserMessage(trimmed, contextId, taskId);

    try {
      await streamMessage(client, message, handleEvent);
    } catch (err) {
      const messageText = err instanceof Error ? err.message : "Unknown error";
      setError(messageText);
      appendMessage({
        id: crypto.randomUUID(),
        role: "status",
        content: `Error: ${messageText}`,
      });
    } finally {
      setIsSending(false);
    }
  };

  const sessionOptions = useMemo<SelectOption[]>(() => {
    return sessionList.map((session) => ({
      name: session.sessionId,
      description: new Date(session.updatedAt).toLocaleString(),
      value: session.sessionId,
    }));
  }, [sessionList]);

  const [selectedSessionIndex, setSelectedSessionIndex] = useState(0);

  const restoreSession = async (sessionId: string) => {
    try {
      const payload = await fetchSession(serverUrl, sessionId);
      setContextId(payload.session.sessionId);
      setTaskId(undefined);
      setMessages(payload.messages);
      setError(null);
      payload.events.forEach(handleEvent);
      setStatusText("Restored session");
      streamingOutputRef.current = false;
      finalOutputRenderedRef.current = false;
      assistantMessageIdRef.current = null;
      setSessionError(null);
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to restore session");
    }
  };

  return (
    <box style={{ flexDirection: "row", padding: 1, height: "100%", width: "100%" }}>
      <box style={{ width: 32, marginRight: 1 }}>
        <StatusPanel
          serverUrl={serverUrl}
          connected={connected}
          agentName={agentName}
          statusText={statusText}
          error={error}
          taskId={taskId}
          contextId={contextId}
        />
      </box>
      <box style={{ flexGrow: 1 }}>
        <ChatPanel
          messages={messages}
          inputKey={inputKey}
          inputRef={inputRef}
          onInput={setInputValue}
          onSend={handleSend}
          isSending={isSending}
          commandHint="/sessions to restore a session"
          inputFocused={!showSessionPicker}
        />
        {showSessionPicker ? (
          <box
            style={{
              position: "absolute",
              left: 8,
              top: 4,
              width: 60,
              height: 16,
              border: true,
              padding: 1,
              backgroundColor: "#0f172a",
            }}
            title="Restore Session"
          >
            <text content="Select a session and press Enter" />
            <select
              key="session-picker"
              focused
              options={sessionOptions}
              selectedIndex={selectedSessionIndex}
              style={{ flexGrow: 1, marginTop: 1 }}
              onSelect={(index, option) => {
                setSelectedSessionIndex(index);
                if (!option?.value) {
                  return;
                }
                void restoreSession(String(option.value));
                setShowSessionPicker(false);
                setTimeout(() => inputRef.current?.focus(), 0);
              }}
            />
            {sessionError ? <text content={`Error: ${sessionError}`} /> : null}
            <text content="Enter to restore • Esc to close" />
          </box>
        ) : null}
      </box>
    </box>
  );
};
