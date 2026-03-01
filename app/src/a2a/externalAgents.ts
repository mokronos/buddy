import { DEFAULT_A2A_BASE_URL } from "~/a2a/client";
import { readJson } from "~/a2a/http";
import {
  ExternalAgentResponseSchema,
  ListExternalAgentsResponseSchema,
  OkResponseSchema,
  type ExternalAgentPayload,
} from "~/a2a/schemas";

export type ExternalAgent = ExternalAgentPayload;

export interface ExternalAgentCreateInput {
  agent_id: string;
  base_url: string;
  use_legacy_card_path: boolean;
}

export interface ExternalAgentUpdateInput {
  base_url: string;
  use_legacy_card_path: boolean;
}

export async function listExternalAgents(): Promise<ExternalAgent[]> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/external`);
  const payload = await readJson(response, ListExternalAgentsResponseSchema);
  return payload.agents;
}

export async function createExternalAgent(input: ExternalAgentCreateInput): Promise<ExternalAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/external`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(input),
  });
  const payload = await readJson(response, ExternalAgentResponseSchema);
  return payload.agent;
}

export async function updateExternalAgent(agentId: string, input: ExternalAgentUpdateInput): Promise<ExternalAgent> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/external/${agentId}`, {
    method: "PUT",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify(input),
  });
  const payload = await readJson(response, ExternalAgentResponseSchema);
  return payload.agent;
}

export async function deleteExternalAgent(agentId: string): Promise<void> {
  const response = await fetch(`${DEFAULT_A2A_BASE_URL}/agents/external/${agentId}`, {
    method: "DELETE",
  });
  await readJson(response, OkResponseSchema);
}
