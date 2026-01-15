import type { RefObject } from "react";
import type { RefObject } from "react";
import type { InputRenderable } from "@opentui/core";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "status";
  content: string;
  streaming?: boolean;
};

type ChatPanelProps = {
  messages: ChatMessage[];
  inputKey: number;
  inputRef: RefObject<InputRenderable | null>;
  onInput: (value: string) => void;
  onSend: (value: string) => void;
  isSending: boolean;
};

const roleLabel = (role: ChatMessage["role"]) => {
  if (role === "user") {
    return "You";
  }
  if (role === "status") {
    return "Status";
  }
  return "Agent";
};

export const ChatPanel = ({
  messages,
  inputKey,
  inputRef,
  onInput,
  onSend,
  isSending,
}: ChatPanelProps) => {
  return (
    <box style={{ border: true, flexDirection: "column", padding: 1, height: "100%" }} title="Chat">
      <scrollbox style={{ flexGrow: 1 }} focused>
        {messages.length === 0 ? (
          <text content="No messages yet. Send one below." />
        ) : (
          messages.map((message) => (
            <text
              key={message.id}
              content={`${roleLabel(message.role)}: ${message.content}${message.streaming ? "▌" : ""}`}
            />
          ))
        )}
      </scrollbox>
      <box style={{ marginTop: 1, height: 3 }}>
        <input
          ref={inputRef}
          key={inputKey}
          placeholder="Type a message and press Enter"
          onInput={onInput}
          onSubmit={onSend}
          focused
        />
      </box>
      <box style={{ marginTop: 1 }}>
        <text content={isSending ? "Sending..." : "Enter to send • ESC to quit"} />
        <text content="/connect to retry server connection" />
      </box>
    </box>
  );
};
