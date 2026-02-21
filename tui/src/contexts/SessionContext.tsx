import type { SelectOption } from "@opentui/core";
import { createContext, createMemo, createSignal, useContext } from "solid-js";

import { fetchSession, fetchSessions } from "../utils/a2a-client";
import type { SessionRestorePayload, SessionSummary } from "../utils/a2a-client";

export type SessionContextValue = {
  sessionList: () => SessionSummary[];
  sessionOptions: () => SelectOption[];
  showSessionPicker: () => boolean;
  sessionError: () => string | null;
  selectedSessionIndex: () => number;
  setShowSessionPicker: (value: boolean) => void;
  setSessionError: (value: string | null) => void;
  setSelectedSessionIndex: (value: number) => void;
  loadSessions: (baseUrl: string) => Promise<void>;
  restoreSession: (baseUrl: string, sessionId: string) => Promise<SessionRestorePayload>;
};

const SessionContext = createContext<SessionContextValue>();

type SessionProviderProps = {
  children: unknown;
};

export const SessionProvider = (props: SessionProviderProps) => {
  const [sessionList, setSessionList] = createSignal<SessionSummary[]>([]);
  const [showSessionPicker, setShowSessionPicker] = createSignal(false);
  const [sessionError, setSessionError] = createSignal<string | null>(null);
  const [selectedSessionIndex, setSelectedSessionIndex] = createSignal(0);

  const sessionOptions = createMemo<SelectOption[]>(() =>
    sessionList().map((session) => ({
      name: session.sessionId,
      description: new Date(session.updatedAt).toLocaleString(),
      value: session.sessionId,
    })),
  );

  const loadSessions = async (baseUrl: string) => {
    try {
      const sessions = await fetchSessions(baseUrl);
      setSessionList(sessions);
      setSessionError(null);
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to load sessions");
      throw err;
    }
  };

  const restoreSession = async (baseUrl: string, sessionId: string): Promise<SessionRestorePayload> => {
    try {
      const payload = await fetchSession(baseUrl, sessionId);
      setSessionError(null);
      return payload;
    } catch (err) {
      setSessionError(err instanceof Error ? err.message : "Failed to restore session");
      throw err;
    }
  };

  const value: SessionContextValue = {
    sessionList,
    sessionOptions,
    showSessionPicker,
    sessionError,
    selectedSessionIndex,
    setShowSessionPicker,
    setSessionError,
    setSelectedSessionIndex,
    loadSessions,
    restoreSession,
  };

  return <SessionContext.Provider value={value}>{props.children}</SessionContext.Provider>;
};

export const useSessions = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSessions must be used within SessionProvider");
  }
  return context;
};
