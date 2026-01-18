import type { SelectOption } from "@opentui/core";
import { For, Show } from "solid-js";

import type { ChatMessage } from "../contexts/ChatContext";
import type { InputHandle } from "../app/useChatInput";

type ChatPanelProps = {
  messages: () => ChatMessage[];
  inputKey: number;
  setInputRef: (value: unknown) => void;
  onInput: (value: string) => void;
  onSend: (value: string) => void;
  onInputKeyDown?: (key: { name: string; ctrl?: boolean }) => void;
  isSending: boolean;
  commandHint?: string;
  inputFocused?: boolean;
  showCommandPicker?: boolean;
  commandOptions?: SelectOption[];
  commandSelectedIndex?: number;
  commandPickerKey?: string;
  onSelectCommand?: (index: number, option: SelectOption | null) => void;
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
  setInputRef,
  onInput,
  onSend,
  isSending,
  commandHint,
  inputFocused = true,
  showCommandPicker = false,
  commandOptions = [],
  commandSelectedIndex = 0,
  commandPickerKey = "command-picker",
  onSelectCommand,
  onInputKeyDown,
}: ChatPanelProps) => {
  const commandPickerStyle = {
    position: "absolute",
    left: 2,
    right: 2,
    bottom: 6,
    height: Math.min(12, Math.max(6, commandOptions.length + 5)),
  };

  return (
    <box style={{ border: true, flexDirection: "column", padding: 1, height: "100%" }} title="Chat">
      <scrollbox style={{ flexGrow: 1 }} focused>
        <Show when={messages().length > 0} fallback={<text content="No messages yet. Send one below." />}>
          <For each={messages()}>
            {(message) => (
              <text
                content={`${roleLabel(message.role)}: ${message.content}${message.streaming ? "▌" : ""}`}
                style={{ fg: roleColor(message.role) }}
              />
            )}
          </For>
        </Show>
      </scrollbox>
      <box style={{ marginTop: 1, height: 3, zIndex: 2 }}>
        <input
          ref={(node) => {
            if (node) {
              setInputRef(node as InputHandle);
            }
          }}
          key={inputKey}
          placeholder="Type a message and press Enter"
          onInput={onInput}
          onSubmit={onSend}
          onKeyDown={onInputKeyDown}
          focused={inputFocused}
        />
      </box>
      <Show when={showCommandPicker}>
        <box
          style={{
            ...commandPickerStyle,
            border: true,
            padding: 1,
            backgroundColor: "#0f172a",
            zIndex: 1,
          }}
          title="Commands"
        >
          <select
            key={commandPickerKey}
            options={commandOptions}
            selectedIndex={commandSelectedIndex}
            showDescription={false}
            itemSpacing={0}
            style={{ flexGrow: 1 }}
            onSelect={onSelectCommand}
          />
        </box>
      </Show>

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
