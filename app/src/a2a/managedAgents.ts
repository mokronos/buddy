import { DEFAULT_A2A_BASE_URL } from "~/a2a/client";
import { readJson } from "~/a2a/http";
import {
  ListManagedAgentsResponseSchema,
  ManagedAgentLogsResponseSchema,
  ManagedAgentResponseSchema,
  OkResponseSchema,
  type ManagedAgentPayload,
} from "~/a2a/schemas";

export type ManagedAgent = ManagedAgentPayload;

export interface ManagedAgentCreateInput {
  agent_id: string;
  image: string;
  config_yaml: string;
  container_port: number;
  config_mount_path: string;
}

export interface ManagedAgentLogs {
  agent: ManagedAgent;
  logs: string;
}

export async function listManagedAgents(): Promise<ManagedAgent[]> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed`);
  const payload = await readJson(response, ListManagedAgentsResponseSchema);
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
  const payload = await readJson(response, ManagedAgentResponseSchema);
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
  const payload = await readJson(response, ManagedAgentResponseSchema);
  return payload.agent;
}

export async function stopManagedAgent(agentId: string): Promise<ManagedAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed/${agentId}/stop`, {
    method: "POST",
  });
  const payload = await readJson(response, ManagedAgentResponseSchema);
  return payload.agent;
}

export async function deleteManagedAgent(agentId: string): Promise<void> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed/${agentId}?removeConfig=true`, {
    method: "DELETE",
  });
  await readJson(response, OkResponseSchema);
}

export async function getManagedAgentLogs(agentId: string, tail: number = 200): Promise<ManagedAgentLogs> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/managed/${agentId}/logs?tail=${tail}`);
  const payload = await readJson(response, ManagedAgentLogsResponseSchema);
  return payload;
}
