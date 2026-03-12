import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";
import type { ManagedCreateFormState } from "~/components/managed-agents/types";

export function createDefaultRuntimeConfig(): RuntimeAgentConfigPayload {
  return {
    agent: {
      id: "demo-agent",
      name: "Demo Agent",
      instructions: "You are a helpful assistant.",
      model: "openrouter:openrouter/free",
    },
    a2a: {
      port: 8000,
      mount_path: "/a2a",
    },
    tools: {
      web_search: true,
      todo: true,
    },
    mcp: {
      enabled: true,
      url: "http://127.0.0.1:18001/mcp",
    },
  };
}

export function createDefaultManagedForm(): ManagedCreateFormState {
  return {
    image: "buddy-agent-runtime:latest",
    config_mount_path: "/etc/buddy/agent.yaml",
    config: createDefaultRuntimeConfig(),
  };
}

export function normalizeMountPath(value: string): string {
  const trimmed = value.trim();
  if (trimmed === "/") {
    return "/";
  }
  return trimmed.replace(/\/+$/, "");
}

export function normalizeRuntimeConfig(config: RuntimeAgentConfigPayload): RuntimeAgentConfigPayload {
  return {
    agent: {
      id: config.agent.id.trim().toLowerCase(),
      name: config.agent.name.trim(),
      instructions: config.agent.instructions.trim(),
      model: config.agent.model.trim(),
    },
    a2a: {
      port: config.a2a.port,
      mount_path: normalizeMountPath(config.a2a.mount_path || "/"),
    },
    tools: {
      web_search: config.tools.web_search,
      todo: config.tools.todo,
    },
    mcp: {
      enabled: config.mcp.enabled,
      url: config.mcp.url.trim(),
    },
  };
}

export function validateRuntimeConfig(
  config: RuntimeAgentConfigPayload,
  options: { lockedAgentId?: string } = {},
): string | null {
  if (config.agent.id.length === 0) {
    return "Agent ID is required";
  }
  if (!/^[a-z0-9][a-z0-9-]*$/.test(config.agent.id)) {
    return "Agent ID must use lowercase letters, numbers, and hyphens only";
  }
  if (options.lockedAgentId && config.agent.id !== options.lockedAgentId) {
    return "Managed agent ID cannot be changed after creation";
  }
  if (config.agent.name.length === 0) {
    return "Agent name is required";
  }
  if (config.agent.instructions.length === 0) {
    return "Instructions are required";
  }
  if (config.agent.model.length === 0) {
    return "Model is required";
  }
  if (!Number.isInteger(config.a2a.port) || config.a2a.port < 1 || config.a2a.port > 65535) {
    return "A2A port must be an integer between 1 and 65535";
  }
  if (config.a2a.mount_path.length === 0 || !config.a2a.mount_path.startsWith("/")) {
    return "A2A mount path must start with '/'";
  }
  if (config.mcp.enabled && config.mcp.url.length === 0) {
    return "MCP URL is required when MCP is enabled";
  }
  return null;
}
