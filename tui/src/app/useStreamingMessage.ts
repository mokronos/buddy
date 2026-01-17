import type { StreamEvent } from "../utils/a2a-client";

export const useStreamingMessage = (
  appendMessage: (message: { id: string; role: "user" | "assistant" | "status"; content: string; streaming?: boolean }) => void,
  updateMessage: (id: string, updater: (message: any) => any) => void,
) => {
  let assistantMessageId: string | null = null;
  let streamingOutput = false;
  let finalOutputRendered = false;

  const ensureAssistantMessage = (content: string) => {
    if (!assistantMessageId) {
      const id = crypto.randomUUID();
      assistantMessageId = id;
      appendMessage({ id, role: "assistant", content, streaming: true });
      return id;
    }

    updateMessage(assistantMessageId, (message) => ({
      ...message,
      content: message.content + content,
      streaming: true,
    }));

    return assistantMessageId;
  };

  const finalizeStreamingMessage = (content?: string) => {
    if (!assistantMessageId) {
      return;
    }

    updateMessage(assistantMessageId, (message) => ({
      ...message,
      content: content ?? message.content,
      streaming: false,
    }));
    assistantMessageId = null;
    streamingOutput = false;
  };

  const handleStreamEvent = (event: StreamEvent, handleEvent: (event: unknown) => void) => {
    if (!event || typeof event !== "object" || !("kind" in event)) {
      return;
    }

    handleEvent(event);

    if (event.kind !== "artifact-update") {
      if (event.kind === "status-update" && event.final && event.status.state !== "input-required") {
        finalizeStreamingMessage();
      }
      return;
    }

    const artifactName = event.artifact.name ?? "";
    const text = (event.artifact.parts ?? [])
      .filter((part) => part.kind === "text")
      .map((part) => part.text ?? "")
      .join("");
    if (!text) {
      return;
    }

    if (artifactName === "output_start") {
      return;
    }

    if (artifactName === "output_delta") {
      streamingOutput = true;
      ensureAssistantMessage(text);
      return;
    }

    if (artifactName === "output_end" || artifactName === "full_output") {
      if (streamingOutput) {
        if (assistantMessageId) {
          finalizeStreamingMessage(text);
        } else {
          appendMessage({ id: crypto.randomUUID(), role: "assistant", content: text });
        }
        finalOutputRendered = true;
        return;
      }

      if (finalOutputRendered) {
        return;
      }

      finalOutputRendered = true;
      appendMessage({ id: crypto.randomUUID(), role: "assistant", content: text });
      return;
    }

    appendMessage({ id: crypto.randomUUID(), role: "assistant", content: text });
  };

  const resetStreamingState = () => {
    assistantMessageId = null;
    streamingOutput = false;
    finalOutputRendered = false;
  };

  return { handleStreamEvent, resetStreamingState };
};
