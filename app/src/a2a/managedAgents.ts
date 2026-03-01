import { DEFAULT_A2A_BASE_URL } from "~/a2a/client";

export interface ManagedAgent {
  agent_id: string;
  image: string;
  config_path: string;
  config_mount_path: string;
  container_port: number;
  container_id: string | null;
  host_port: number | null;
  status: string;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ManagedAgentCreateInput {
  agent_id: string;
  image: string;
  config_yaml: string;
  container_port: number;
  config_mount_path: string;
}

interface ListManagedAgentsResponse {
  agents: ManagedAgent[];
}

interface ManagedAgentResponse {
  agent: ManagedAgent;
}

interface ManagedAgentLogsResponse {
  agent: ManagedAgent;
  logs: string;
}

export interface ManagedAgentLogs {
  agent: ManagedAgent;
  logs: string;
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function listManagedAgents(): Promise<ManagedAgent[]> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed`);
  const payload = await readJson<ListManagedAgentsResponse>(response);
  return payload.agents;
}

export async function createManagedAgent(input: ManagedAgentCreateInput): Promise<ManagedAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(input),
  });
  const payload = await readJson<ManagedAgentResponse>(response);
  return payload.agent;
}

export async function startManagedAgent(agentId: string): Promise<ManagedAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed/${agentId}/start`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({}),
  });
  const payload = await readJson<ManagedAgentResponse>(response);
  return payload.agent;
}

export async function stopManagedAgent(agentId: string): Promise<ManagedAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed/${agentId}/stop`, {
    method: "POST",
  });
  const payload = await readJson<ManagedAgentResponse>(response);
  return payload.agent;
}

export async function deleteManagedAgent(agentId: string): Promise<void> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed/${agentId}?removeConfig=true`, {
    method: "DELETE",
  });
  await readJson<{ ok: boolean }>(response);
}

export async function getManagedAgentLogs(agentId: string, tail: number = 200): Promise<ManagedAgentLogs> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed/${agentId}/logs?tail=${tail}`);
  const payload = await readJson<ManagedAgentLogsResponse>(response);
  return payload;
}
