import { z } from "zod";

const StringOrNullSchema = z.string().nullable();

export const AgentEndpointSchema = z.object({
  key: z.string(),
  name: z.string(),
  mountPath: z.string(),
  agentCardPath: z.string(),
  url: z.string(),
});

export const AgentsIndexResponseSchema = z.object({
  defaultAgentKey: z.string().nullable().optional(),
  agents: z.array(AgentEndpointSchema),
});

export const AgentCardSkillSchema = z.object({
  name: z.string().optional(),
  id: z.string().optional(),
});

export const AgentCardSchema = z.object({
  description: StringOrNullSchema.optional(),
  version: StringOrNullSchema.optional(),
  skills: z.array(AgentCardSkillSchema).optional(),
});

export const ManagedAgentSchema = z.object({
  agent_id: z.string(),
  image: z.string(),
  config_path: z.string(),
  config_mount_path: z.string(),
  container_port: z.number(),
  container_id: StringOrNullSchema,
  host_port: z.number().nullable(),
  status: z.string(),
  last_error: StringOrNullSchema,
  created_at: z.string(),
  updated_at: z.string(),
});

export const ListManagedAgentsResponseSchema = z.object({
  agents: z.array(ManagedAgentSchema),
});

export const ManagedAgentResponseSchema = z.object({
  agent: ManagedAgentSchema,
});

export const ManagedAgentLogsResponseSchema = z.object({
  agent: ManagedAgentSchema,
  logs: z.string(),
});

export const ManagedAgentConfigResponseSchema = z.object({
  configYaml: z.string(),
});

export const ExternalAgentSchema = z.object({
  agent_id: z.string(),
  base_url: z.string(),
  use_legacy_card_path: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const ListExternalAgentsResponseSchema = z.object({
  agents: z.array(ExternalAgentSchema),
});

export const ExternalAgentResponseSchema = z.object({
  agent: ExternalAgentSchema,
});

export const OkResponseSchema = z.object({
  ok: z.boolean(),
});

export type AgentEndpointPayload = z.infer<typeof AgentEndpointSchema>;
export type AgentsIndexResponsePayload = z.infer<typeof AgentsIndexResponseSchema>;
export type AgentCardPayload = z.infer<typeof AgentCardSchema>;
export type ManagedAgentPayload = z.infer<typeof ManagedAgentSchema>;
export type ManagedAgentLogsPayload = z.infer<typeof ManagedAgentLogsResponseSchema>;
export type ManagedAgentConfigPayload = z.infer<typeof ManagedAgentConfigResponseSchema>;
export type ExternalAgentPayload = z.infer<typeof ExternalAgentSchema>;
