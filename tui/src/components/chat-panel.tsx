import type { RefObject } from "react";
import type { InputRenderable, SelectOption } from "@opentui/core";

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
  inputRef,
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
       <box style={{ marginTop: 1, height: 3, zIndex: 2 }}>

        <input
          ref={inputRef}
          key={inputKey}
          placeholder="Type a message and press Enter"
          onInput={onInput}
          onSubmit={onSend}
          onKeyDown={onInputKeyDown}
          focused={inputFocused}
        />
      </box>
       {showCommandPicker ? (
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
             keyBindings={[]}
           />
         </box>
       ) : null}

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
