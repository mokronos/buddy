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
  commandHint?: string;
  inputFocused?: boolean;
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

const roleColor = (role: ChatMessage["role"]) => {
  if (role === "user") {
    return "#7aa2f7";
  }
  if (role === "status") {
    return "#f6c177";
  }
  return "#9ece6a";
};

export const ChatPanel = ({
  messages,
  inputKey,
  inputRef,
  onInput,
  onSend,
  isSending,
  commandHint,
  inputFocused = true,
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
              style={{ fg: roleColor(message.role) }}
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
          focused={inputFocused}
        />
      </box>
      <box style={{ marginTop: 1 }}>
        <text
          content={[
            isSending ? "Sending..." : "Enter to send • Ctrl+C to quit",
            "/connect to retry server connection",
            commandHint,
          ]
            .filter(Boolean)
            .join("\n")}
        />
      </box>
    </box>
  );
};
