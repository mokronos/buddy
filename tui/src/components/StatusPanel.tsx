import { Show } from "solid-js";

type StatusPanelProps = {
  serverUrl: string;
  connected: boolean;
  agentName: string;
  statusText: string;
  error: string | null;
  taskId?: string;
  contextId?: string;
};

export const StatusPanel = (props: StatusPanelProps) => {
  return (
    <box style={{ border: true, flexDirection: "column", padding: 1, height: "100%" }} title="Status">
      <text content={`Server: ${props.serverUrl}`} />
      <text content={`Connection: ${props.connected ? "Connected" : "Disconnected"}`} />
      <text content={`Agent: ${props.agentName}`} />
      <text content={`State: ${props.statusText}`} />
      <Show when={props.taskId} fallback={<text content="Task: (none)" />}>
        <text content={`Task: ${props.taskId}`} />
      </Show>
      <Show when={props.contextId} fallback={<text content="Context: (none)" />}>
        <text content={`Context: ${props.contextId}`} />
      </Show>
      <Show when={props.error}>
        <text content={`Error: ${props.error}`} />
      </Show>
      <text content="Ctrl+C to quit." />
    </box>
  );
};
