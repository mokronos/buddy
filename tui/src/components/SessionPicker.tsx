import type { SelectKeyBinding, SelectOption } from "@opentui/core";

const SELECT_KEY_BINDINGS = [
  { name: "up", action: "move-up" },
  { name: "down", action: "move-down" },
  { name: "n", ctrl: true, action: "move-down" },
  { name: "p", ctrl: true, action: "move-up" },
  { name: "enter", action: "select-current" },
] satisfies SelectKeyBinding[];

type SessionPickerProps = {
  sessionOptions: SelectOption[];
  selectedSessionIndex: number;
  sessionError: string | null;
  onSelectSession: (index: number, option: SelectOption | null) => void;
};

export const SessionPicker = (props: SessionPickerProps) => {
  return (
    <box
      style={{
        position: "absolute",
        left: 8,
        top: 4,
        width: 60,
        height: 16,
        border: true,
        padding: 1,
        backgroundColor: "#0f172a",
      }}
      title="Restore Session"
    >
      <text content="Select a session and press Enter" />
      <select
        key="session-picker"
        focused
        options={props.sessionOptions}
        selectedIndex={props.selectedSessionIndex}
        style={{ flexGrow: 1, marginTop: 1 }}
        keyBindings={SELECT_KEY_BINDINGS}
        onSelect={props.onSelectSession}
      />
      {props.sessionError ? <text content={`Error: ${props.sessionError}`} /> : null}
      <text content="Enter to restore • Esc to close" />
    </box>
  );
};
