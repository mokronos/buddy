import type { AgentCard } from "@a2a-js/sdk";
import type { A2AClient } from "@a2a-js/sdk/client";

export const fetchAgentCard = async (client: A2AClient): Promise<AgentCard> => {
  return client.getAgentCard();
};
