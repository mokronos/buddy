import { createContext, createMemo, createSignal, onCleanup, useContext } from "solid-js";

import { createA2AClient } from "../utils/a2a-client";

export type ConnectionContextValue = {
  serverUrl: () => string;
  restBaseUrl: () => string;
  agentName: () => string;
  connected: () => boolean;
  statusText: () => string;
  error: () => string | null;
  taskId: () => string | undefined;
  contextId: () => string | undefined;
  client: () => ReturnType<typeof createA2AClient> | null;
  setError: (value: string | null) => void;
  setTaskId: (value: string | undefined) => void;
  setContextId: (value: string | undefined) => void;
  setStatusText: (value: string) => void;
  connectToServer: () => Promise<void>;
  handleEvent: (event: unknown) => void;
  inputRef: () => unknown;
  setInputRef: (value: unknown) => void;
  resetConnection: () => void;
};

const ConnectionContext = createContext<ConnectionContextValue>();

const DEFAULT_SERVER_URL = process.env.TUI_SERVER_URL ?? "http://localhost:10001/a2a";

type ConnectionProviderProps = {
  children: unknown;
};

export const ConnectionProvider = (props: ConnectionProviderProps) => {
  const [serverUrl] = createSignal(DEFAULT_SERVER_URL);
  const restBaseUrl = createMemo(() => serverUrl().replace(/\/a2a\/?$/, ""));
  const [agentName, setAgentName] = createSignal("Unknown Agent");
  const [connected, setConnected] = createSignal(false);
  const [statusText, setStatusText] = createSignal("Disconnected");
  const [error, setError] = createSignal<string | null>(null);
  const [taskId, setTaskId] = createSignal<string | undefined>(undefined);
  const [contextId, setContextId] = createSignal<string | undefined>(undefined);
  const [client, setClient] = createSignal<ReturnType<typeof createA2AClient> | null>(null);
  const [inputRef, setInputRef] = createSignal<unknown>(null);

  const connectToServer = async () => {
    const clientInstance = createA2AClient(serverUrl());
    setClient(clientInstance);
    setStatusText("Connecting...");

    setConnected(true);
    setAgentName("Agent");
    setError(null);
    setStatusText("Connected");
  };

  const handleEvent = (event: unknown) => {
    if (!event || typeof event !== "object" || !("kind" in event)) {
      return;
    }

    const typedEvent = event as {
      kind: string;
      taskId?: string;
      contextId?: string;
      id?: string;
      final?: boolean;
      status?: { state?: string; message?: { parts?: { kind: string; text?: string }[] } };
      artifact?: { name?: string; parts?: { kind: string; text?: string }[] };
    };

    if (typedEvent.kind === "message") {
      if (typedEvent.taskId) {
        setTaskId(typedEvent.taskId);
      }
      if (typedEvent.contextId) {
        setContextId(typedEvent.contextId);
      }
      return;
    }

    if (typedEvent.kind === "status-update" && typedEvent.status) {
      const stateText = typedEvent.status.state ?? "unknown";
      setStatusText(stateText);
      if (typedEvent.taskId) {
        setTaskId(typedEvent.taskId);
      }
      if (typedEvent.contextId) {
        setContextId(typedEvent.contextId);
      }
      if (typedEvent.final && typedEvent.status.state !== "input-required") {
        setTaskId(undefined);
      }
      return;
    }

    if (typedEvent.kind === "task") {
      if (typedEvent.id) {
        setTaskId(typedEvent.id);
      }
      if (typedEvent.contextId) {
        setContextId(typedEvent.contextId);
      }
    }
  };

  onCleanup(() => {
    setClient(null);
  });

  const resetConnection = () => {
    setClient(null);
    setStatusText("Disconnected");
    setConnected(false);
  };

  const value: ConnectionContextValue = {
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
    setStatusText,
    connectToServer,
    handleEvent,
    inputRef,
    setInputRef,
    resetConnection,
  };

  return <ConnectionContext.Provider value={value}>{props.children}</ConnectionContext.Provider>;
};

export const useConnection = () => {
  const context = useContext(ConnectionContext);
  if (!context) {
    throw new Error("useConnection must be used within ConnectionProvider");
  }
  return context;
};
