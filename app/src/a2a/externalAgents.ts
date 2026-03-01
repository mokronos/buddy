import { DEFAULT_A2A_BASE_URL } from "~/a2a/client";

export interface ExternalAgent {
  agent_id: string;
  base_url: string;
  use_legacy_card_path: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExternalAgentCreateInput {
  agent_id: string;
  base_url: string;
  use_legacy_card_path: boolean;
}

export interface ExternalAgentUpdateInput {
  base_url: string;
  use_legacy_card_path: boolean;
}

interface ListExternalAgentsResponse {
  agents: ExternalAgent[];
}

interface ExternalAgentResponse {
  agent: ExternalAgent;
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function listExternalAgents(): Promise<ExternalAgent[]> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/external-agents`);
  const payload = await readJson<ListExternalAgentsResponse>(response);
  return payload.agents;
}

export async function createExternalAgent(input: ExternalAgentCreateInput): Promise<ExternalAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/external-agents`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(input),
  });
  const payload = await readJson<ExternalAgentResponse>(response);
  return payload.agent;
}

export async function updateExternalAgent(agentId: string, input: ExternalAgentUpdateInput): Promise<ExternalAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/external-agents/${agentId}`, {
    method: "PUT",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(input),
  });
  const payload = await readJson<ExternalAgentResponse>(response);
  return payload.agent;
}

export async function deleteExternalAgent(agentId: string): Promise<void> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/external-agents/${agentId}`, {
    method: "DELETE",
  });
  await readJson<{ ok: boolean }>(response);
}
