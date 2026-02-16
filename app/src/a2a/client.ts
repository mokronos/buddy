import { ClientFactory, type Client } from "@a2a-js/sdk/client";
import type { MessageSendParams } from "@a2a-js/sdk";

const DEFAULT_A2A_BASE_URL = "http://localhost:10001";

export interface A2AClientConfig {
  baseUrl?: string;
  agentCardPath?: string;
}

export interface A2AStreamEvent {
  kind: string;
  [key: string]: unknown;
}

export class A2AClient {
  private readonly factory = new ClientFactory();
  private clientPromise: Promise<Client> | null = null;

  constructor(private readonly config: A2AClientConfig = {}) {}

  private getClient(): Promise<Client> {
    if (!this.clientPromise) {
      this.clientPromise = this.factory.createFromUrl(
        this.config.baseUrl ?? DEFAULT_A2A_BASE_URL,
        this.config.agentCardPath,
      );
    }

    return this.clientPromise;
  }

  async sendMessageStream(
    params: MessageSendParams,
    onEvent: (event: A2AStreamEvent) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    const client = await this.getClient();
    const stream = client.sendMessageStream(params, { signal });

    for await (const event of stream) {
      onEvent(event as A2AStreamEvent);
    }
  }
}

export function createA2AClient(config?: A2AClientConfig): A2AClient {
  return new A2AClient(config);
}
