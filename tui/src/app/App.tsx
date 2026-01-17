import { useKeyboard } from "@opentui/solid";
import { createEffect, onCleanup } from "solid-js";

import { ChatPanel } from "../components/ChatPanel";
import { SessionPicker } from "../components/SessionPicker";
import { StatusPanel } from "../components/StatusPanel";
import { useChat } from "../contexts/ChatContext";
import { useConnection } from "../contexts/ConnectionContext";
import { useSessions } from "../contexts/SessionContext";
import { buildUserMessage, streamMessage } from "../utils/a2a-client";
import { shouldShowCommandPicker, toCommandInput } from "../utils/commands";
import { handleCommandNavigation, useCommandPicker } from "./useCommandPicker";
import { handleCtrlW, useChatInput } from "./useChatInput";
import { useStreamingMessage } from "./useStreamingMessage";

import type { InputHandle } from "./useChatInput";

export const App = () => {
  const { messages, appendMessage, updateMessage, replaceMessages } = useChat();
  const { handleStreamEvent: handleStreamingEvent, resetStreamingState } = useStreamingMessage(
    appendMessage,
    updateMessage,
  );

  const handleEventWithStatus = (event: unknown) => {
    handleEvent(event);

    if (!event || typeof event !== "object" || !("kind" in event)) {
      return;
    }

    const typedEvent = event as {
      kind: string;
      status?: { message?: { parts?: { kind: string; text?: string }[] } };
    };

    if (typedEvent.kind === "status-update" && typedEvent.status?.message?.parts) {
      const statusMessage = typedEvent.status.message.parts
        .filter((part) => part.kind === "text")
        .map((part) => part.text ?? "")
        .join("");
      if (statusMessage) {
        appendMessage({ id: crypto.randomUUID(), role: "status", content: statusMessage });
      }
    }

    if (typedEvent.kind === "task" && typedEvent.status?.message?.parts) {
      const statusMessage = typedEvent.status.message.parts
        .filter((part) => part.kind === "text")
        .map((part) => part.text ?? "")
        .join("");
      if (statusMessage) {
        appendMessage({ id: crypto.randomUUID(), role: "status", content: statusMessage });
      }
    }
  };

  const {
    serverUrl,
    restBaseUrl,
    agentName,
    connected,
    statusText,
    error,
    taskId,
    contextId,
    client,
    setError,
    setTaskId,
    setContextId,
    connectToServer,
    handleEvent,
    resetConnection,
    inputRef,
    setInputRef,
  } = useConnection();
  const {
    sessionOptions,
    showSessionPicker,
    sessionError,
    selectedSessionIndex,
    setShowSessionPicker,
    setSelectedSessionIndex,
    loadSessions,
    restoreSession,
  } = useSessions();

  const {
    inputValue,
    setInputValue,
    inputKey,
    setInputKey,
    isSending,
    setIsSending,
  } = useChatInput();

  const {
    filteredCommands,
    commandOptions,
    commandPickerKey,
    showCommandPicker,
    setShowCommandPicker,
    selectedCommandIndex,
    setSelectedCommandIndex,
    showCommandPickerResolved,
  } = useCommandPicker(inputValue);

  createEffect(() => {
    const shouldShow = shouldShowCommandPicker(inputValue()) && !showSessionPicker();
    setShowCommandPicker(shouldShow);
    if (shouldShow) {
      setSelectedCommandIndex(0);
    }
  });

  useKeyboard((key) => {
    if (showSessionPicker() && key.name === "escape") {
      setShowSessionPicker(false);
      setTimeout(() => (inputRef() as InputHandle | null)?.focus?.(), 0);
      return;
    }

    if (showSessionPicker()) {
      return;
    }

    if (
      handleCommandNavigation(
        key,
        showCommandPickerResolved,
        commandOptions,
        selectedCommandIndex,
        setSelectedCommandIndex,
        setShowCommandPicker,
        filteredCommands,
      )
    ) {
      return;
    }

    if (key.ctrl && key.name === "w") {
      handleCtrlW(inputRef() as InputHandle | null);
    }
  });

  const handleSend = async (value: string) => {
    const clientInstance = client();
    const trimmed = value.trim();
    if (!trimmed) {
      return;
    }

    if (showCommandPickerResolved()) {
      const selected = filteredCommands()[selectedCommandIndex()];
      if (selected) {
        const input = inputRef() as InputHandle | null;
        if (input) {
          input.value = toCommandInput(selected);
          input.cursorPosition = input.value.length;
          setInputValue(input.value);
        }
      }
      setShowCommandPicker(false);
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

    if (!clientInstance) {
      return;
    }

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    appendMessage(userMessage);

    const input = inputRef() as InputHandle | null;
    if (input) {
      input.value = "";
      input.cursorPosition = 0;
    }
    setInputValue("");
    setInputKey((prev) => prev + 1);
    setIsSending(true);
    setError(null);
    resetStreamingState();

    const message = buildUserMessage(trimmed, contextId(), taskId());

    try {
      await streamMessage(clientInstance, message, (event) => handleStreamingEvent(event, handleEventWithStatus));
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

  const handleSelectCommand = (index: number, option: { value?: unknown } | null) => {
    setSelectedCommandIndex(index);
    if (!option) {
      return;
    }
    const selected = filteredCommands()[index];
    if (!selected) {
      return;
    }
    const input = inputRef() as InputHandle | null;
    if (input) {
      input.value = toCommandInput(selected);
      input.cursorPosition = input.value.length;
      setInputValue(input.value);
    }
    setShowCommandPicker(false);
  };

  const handleSessionSelect = (index: number, option: { value?: unknown } | null) => {
    setSelectedSessionIndex(index);
    if (!option?.value) {
      return;
    }

    void (async () => {
      try {
        const payload = await restoreSession(restBaseUrl(), String(option.value));
        setContextId(payload.session.sessionId);
        setTaskId(undefined);
        replaceMessages(payload.messages);
        setStatusText("Restored session");

        payload.events.forEach((event) => {
          if (event.kind === "task") {
            if (event.contextId) {
              setContextId(event.contextId);
            }
            if (event.id) {
              setTaskId(event.id);
            }
          }
          if (event.kind === "status-update" && event.status.state) {
            setStatusText(event.status.state);
          }
        });
      } catch {
      }
      setShowSessionPicker(false);
    })();
  };

  createEffect(() => {
    void connectToServer();
  });

  createEffect(() => {
    if (showSessionPicker()) {
      void loadSessions(restBaseUrl());
    }
  });

  onCleanup(() => {
    setShowCommandPicker(false);
    resetConnection();
  });

  return (
    <box style={{ flexDirection: "row", padding: 1, height: "100%", width: "100%" }}>
      <box style={{ width: 32, marginRight: 1 }}>
        <StatusPanel
          serverUrl={serverUrl()}
          connected={connected()}
          agentName={agentName()}
          statusText={statusText()}
          error={error()}
          taskId={taskId()}
          contextId={contextId()}
        />
      </box>
      <box style={{ flexGrow: 1 }}>
        <ChatPanel
          messages={messages}
          inputKey={inputKey()}
          setInputRef={setInputRef}
          onInput={(value) => {
            setInputValue(value);
          }}
          onSend={handleSend}
          isSending={isSending()}
          commandHint="/sessions to restore a session"
          inputFocused={!showSessionPicker()}
          showCommandPicker={showCommandPickerResolved()}
          commandOptions={commandOptions()}
          commandSelectedIndex={selectedCommandIndex()}
          commandPickerKey={commandPickerKey()}
          onSelectCommand={handleSelectCommand}
        />
        {showSessionPicker() ? (
          <SessionPicker
            sessionOptions={sessionOptions()}
            selectedSessionIndex={selectedSessionIndex()}
            sessionError={sessionError()}
            onSelectSession={handleSessionSelect}
          />
        ) : null}
      </box>
    </box>
  );
};
