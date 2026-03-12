import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";
import type { ManagedCreateFormState } from "~/components/managed-agents/types";

export function createDefaultRuntimeConfig(): RuntimeAgentConfigPayload {
  return {
    agent: {
      name: "Demo Agent",
      instructions: "You are a helpful assistant.",
      model: "openrouter:openrouter/free",
    },
    mcp_servers: [{ url: "http://127.0.0.1:18001/mcp" }],
  };
}

export function createDefaultManagedForm(): ManagedCreateFormState {
  return {
    config: createDefaultRuntimeConfig(),
  };
}

export function normalizeRuntimeConfig(config: RuntimeAgentConfigPayload): RuntimeAgentConfigPayload {
  return {
    agent: {
      name: config.agent.name.trim(),
      instructions: config.agent.instructions.trim(),
      model: config.agent.model.trim(),
    },
    mcp_servers: config.mcp_servers.map((server) => ({
      url: server.url.trim(),
    })),
  };
}

export function validateRuntimeConfig(config: RuntimeAgentConfigPayload): string | null {
  if (config.agent.name.length === 0) {
    return "Agent name is required";
  }
  if (config.agent.instructions.length === 0) {
    return "Instructions are required";
  }
  if (config.agent.model.length === 0) {
    return "Model is required";
  }
  for (let index = 0; index < config.mcp_servers.length; index += 1) {
    if (config.mcp_servers[index].url.length === 0) {
      return `MCP server URL #${index + 1} is required`;
    }
  }
  return null;
}
