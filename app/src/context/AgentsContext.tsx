import { useQueryClient } from "@tanstack/solid-query";
import { createContext, createSignal, useContext, type Accessor, type JSX } from "solid-js";
import { DEFAULT_A2A_BASE_URL } from "~/a2a/client";
import { readJson } from "~/a2a/http";
import { AgentCardSchema, AgentsIndexResponseSchema, type AgentCardPayload } from "~/a2a/schemas";

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

interface AgentsContextValue {
  refreshAgents: () => Promise<void>;
  agents: Accessor<AgentEndpoint[]>;
  activeAgentKey: Accessor<string>;
  activeAgentName: Accessor<string>;
  setActiveAgentKey: (agentKey: string) => void;
}

interface AgentCardDetails {
  description: string | null;
  version: string | null;
  skills: string[];
}

interface AgentsIndexPayload {
  defaultAgentKey: string | null;
  agents: AgentEndpoint[];
}

const AgentsContext = createContext<AgentsContextValue>();

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

export function AgentsProvider(props: { children: JSX.Element }) {
  let refreshRequestId = 0;
  const [agents, setAgents] = createSignal<AgentEndpoint[]>([]);
  const [activeAgentKey, setActiveAgentKeySignal] = createSignal("");
  const [activeAgentName, setActiveAgentName] = createSignal("No agent connected");
  const queryClient = useQueryClient();

  const applyAgentsPayload = (payload: AgentsIndexPayload): void => {
    const requestId = ++refreshRequestId;
    const loadedAgents = payload.agents;

    setAgents(loadedAgents);

    if (loadedAgents.length === 0) {
      setActiveAgentKeySignal("");
      setActiveAgentName("No agent connected");
      return;
    }

    const currentActiveKey = activeAgentKey();
    const fallbackAgentKey =
      typeof payload.defaultAgentKey === "string" && loadedAgents.some((agent) => agent.key === payload.defaultAgentKey)
        ? payload.defaultAgentKey
        : loadedAgents[0].key;
    const nextActiveKey = loadedAgents.some((agent) => agent.key === currentActiveKey) ? currentActiveKey : fallbackAgentKey;
    const nextActiveAgent = loadedAgents.find((agent) => agent.key === nextActiveKey) ?? loadedAgents[0];
    setActiveAgentKeySignal(nextActiveAgent.key);
    setActiveAgentName(nextActiveAgent.name);

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
  };

  const refreshAgents = async (): Promise<void> => {
    try {
      await queryClient.invalidateQueries({ queryKey: ["agents"] });
      const payload = await queryClient.fetchQuery({
        queryKey: ["agents", "index"],
        queryFn: fetchAgentsIndex,
      });
      applyAgentsPayload(payload);
    } catch {
      setAgents([]);
      setActiveAgentKeySignal("");
      setActiveAgentName("No agent connected");
    }
  };

  const setActiveAgentKey = (agentKey: string): void => {
    const selectedAgent = agents().find((agent) => agent.key === agentKey);
    if (!selectedAgent) {
      return;
    }
    setActiveAgentKeySignal(selectedAgent.key);
    setActiveAgentName(selectedAgent.name);
  };

  return (
    <AgentsContext.Provider
      value={{
        refreshAgents,
        agents,
        activeAgentKey,
        activeAgentName,
        setActiveAgentKey,
      }}
    >
      {props.children}
    </AgentsContext.Provider>
  );
}

export function useAgents(): AgentsContextValue {
  const context = useContext(AgentsContext);
  if (!context) {
    throw new Error("useAgents must be used within AgentsProvider");
  }
  return context;
}
