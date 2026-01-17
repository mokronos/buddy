import type { InputRenderable, SelectKeyBinding, SelectOption } from "@opentui/core";
import { useKeyboard } from "@opentui/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
import {
  SLASH_COMMANDS,
  filterSlashCommands,
  shouldShowCommandPicker,
  toCommandInput,
  type SlashCommandWithHandler,
} from "./lib/commands";
import { fetchAgentCard } from "./lib/server-status";

const DEFAULT_SERVER_URL = process.env.TUI_SERVER_URL ?? "http://localhost:10001/a2a";

const SELECT_KEY_BINDINGS = [
  { name: "up", action: "move-up" },
  { name: "down", action: "move-down" },
  { name: "n", ctrl: true, action: "move-down" },
  { name: "p", ctrl: true, action: "move-up" },
  { name: "enter", action: "select-current" },
] satisfies SelectKeyBinding[];

export const App = () => {
  const [serverUrl] = useState(DEFAULT_SERVER_URL);
  const restBaseUrl = serverUrl.replace(/\/a2a\/?$/, "");
  const [agentName, setAgentName] = useState("Unknown Agent");
  const [connected, setConnected] = useState(false);
  const [statusText, setStatusText] = useState("Disconnected");
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [inputKey, setInputKey] = useState(0);
  const [caretIndex, setCaretIndex] = useState(0);
  const [isSending, setIsSending] = useState(false);
  const [taskId, setTaskId] = useState<string | undefined>(undefined);
  const [contextId, setContextId] = useState<string | undefined>(undefined);
  const [sessionList, setSessionList] = useState<SessionSummary[]>([]);
  const [showSessionPicker, setShowSessionPicker] = useState(false);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [showCommandPicker, setShowCommandPicker] = useState(false);
  const [selectedCommandIndex, setSelectedCommandIndex] = useState(0);

  const clientRef = useRef<ReturnType<typeof createA2AClient> | null>(null);
  const inputRef = useRef<InputRenderable | null>(null);
  const assistantMessageIdRef = useRef<string | null>(null);
  const streamingOutputRef = useRef(false);
  const finalOutputRenderedRef = useRef(false);

  const connectToServer = useCallback(async () => {
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
  }, [serverUrl]);

  const commands = useMemo<SlashCommandWithHandler[]>(
    () =>
      SLASH_COMMANDS.map((command) => ({
        ...command,
        run: async () => {
          if (command.name === "connect") {
            setInputValue("");
            setInputKey((prev) => prev + 1);
            await connectToServer();
            return;
          }
          if (command.name === "sessions") {
            setInputValue("");
            setInputKey((prev) => prev + 1);
            setSelectedSessionIndex(0);
            setShowSessionPicker(true);
          }
        },
      })),
    [connectToServer],
  );

  const filteredCommands = useMemo(() => {
    return filterSlashCommands(SLASH_COMMANDS, inputValue).slice(0, 8);
  }, [inputValue]);

  const commandOptions = useMemo(() => {
    return filteredCommands.map((command) => ({
      name: `/${command.name}`,
      description: command.description,
      value: command.name,
    }));
  }, [filteredCommands]);

  const commandPickerKey = useMemo(
    () => `command-picker-${showCommandPicker}-${inputValue}-${commandOptions.length}-${selectedCommandIndex}`,
    [showCommandPicker, inputValue, commandOptions.length, selectedCommandIndex],
  );

  const showCommandPickerResolved = showCommandPicker && commandOptions.length > 0;

  useEffect(() => {
    const shouldShow = shouldShowCommandPicker(inputValue) && !showSessionPicker;
    setShowCommandPicker(shouldShow);
    if (shouldShow) {
      setSelectedCommandIndex(0);
    }
  }, [inputValue, showSessionPicker]);

  useEffect(() => {
    const input = inputRef.current;
    if (input) {
      setCaretIndex(input.cursorPosition ?? (input.value?.length ?? 0));
    }
  }, [inputValue]);

  const handleCommandNavigation = useCallback(
    (key: { name: string; ctrl?: boolean }) => {
      if (!showCommandPickerResolved) {
        return false;
      }

      if (key.ctrl && key.name === "n") {
        setSelectedCommandIndex((prev) => Math.min(prev + 1, commandOptions.length - 1));
        return true;
      }
      if (key.ctrl && key.name === "p") {
        setSelectedCommandIndex((prev) => Math.max(prev - 1, 0));
        return true;
      }
      if (key.name === "up") {
        setSelectedCommandIndex((prev) => Math.max(prev - 1, 0));
        return true;
      }
      if (key.name === "down") {
        setSelectedCommandIndex((prev) => Math.min(prev + 1, commandOptions.length - 1));
        return true;
      }
      if (key.name === "escape") {
        setShowCommandPicker(false);
        return true;
      }
      if (key.name === "enter") {
        const selected = filteredCommands[selectedCommandIndex];
        if (selected) {
          const input = inputRef.current;
          if (input) {
            input.value = toCommandInput(selected);
            input.cursorPosition = input.value.length;
            setInputValue(input.value);
          }
        }
        setShowCommandPicker(false);
        return true;
      }

      return false;
    },
    [commandOptions.length, filteredCommands, selectedCommandIndex, showCommandPickerResolved],
  );

  const handleInputKeyDown = useCallback(
    (key: { name: string; ctrl?: boolean }) => {
      const input = inputRef.current;
      if (input) {
        setCaretIndex(input.cursorPosition ?? (input.value?.length ?? 0));
      }
      handleCommandNavigation(key);
    },
    [handleCommandNavigation],
  );

  useKeyboard((key) => {
    const input = inputRef.current;
    if (input) {
      setCaretIndex(input.cursorPosition ?? (input.value?.length ?? 0));
    }

    if (showSessionPicker && key.name === "escape") {
      setShowSessionPicker(false);
      setTimeout(() => inputRef.current?.focus(), 0);
      return;
    }

    if (showSessionPicker) {
      return;
    }

    if (handleCommandNavigation(key)) {
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

  const loadSessions = async () => {
    try {
      const sessions = await fetchSessions(restBaseUrl);
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
  }, [serverUrl, connectToServer]);

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

    if (showCommandPickerResolved) {
      const selected = filteredCommands[selectedCommandIndex];
      if (selected) {
        const input = inputRef.current;
        if (input) {
          input.value = toCommandInput(selected);
          input.cursorPosition = input.value.length;
          setInputValue(input.value);
        }
      }
      setShowCommandPicker(false);
      return;
    }

    const command = commands.find((item) => `/${item.name}` === trimmed);
    if (command) {
      setShowCommandPicker(false);
      await command.run();
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
      const payload = await fetchSession(restBaseUrl, sessionId);
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
          onInput={(value) => {
            const input = inputRef.current;
            if (input) {
              setCaretIndex(input.cursorPosition ?? value.length);
            }
            setInputValue(value);
          }}
          onSend={handleSend}
          isSending={isSending}
          commandHint="/sessions to restore a session"
          inputFocused={!showSessionPicker}
          showCommandPicker={showCommandPickerResolved}
          commandOptions={commandOptions}
          commandSelectedIndex={selectedCommandIndex}
          commandPickerKey={commandPickerKey}
          onSelectCommand={(index, option) => {
            setSelectedCommandIndex(index);
            if (!option) {
              return;
            }
            const selected = filteredCommands[index];
            if (!selected) {
              return;
            }
            const input = inputRef.current;
            if (input) {
              input.value = toCommandInput(selected);
              input.cursorPosition = input.value.length;
              setInputValue(input.value);
            }
            setShowCommandPicker(false);
          }}
          onInputKeyDown={handleInputKeyDown}
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
              keyBindings={SELECT_KEY_BINDINGS}
             onSelect={(index, option) => {
                 setSelectedSessionIndex(index);
                 if (!option?.value) {
                   return;
                 }
                 void restoreSession(String(option.value));
                 setShowSessionPicker(false);
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
