type StatusPanelProps = {
  serverUrl: string;
  connected: boolean;
  agentName: string;
  statusText: string;
  error: string | null;
  taskId?: string;
  contextId?: string;
};

export const StatusPanel = ({
  serverUrl,
  connected,
  agentName,
  statusText,
  error,
  taskId,
  contextId,
}: StatusPanelProps) => {
  return (
    <box style={{ border: true, flexDirection: "column", padding: 1, height: "100%" }} title="Status">
      <text content={`Server: ${serverUrl}`} />
      <text content={`Connection: ${connected ? "Connected" : "Disconnected"}`} />
      <text content={`Agent: ${agentName}`} />
      <text content={`State: ${statusText}`} />
      {taskId ? <text content={`Task: ${taskId}`} /> : <text content="Task: (none)" />}
      {contextId ? <text content={`Context: ${contextId}`} /> : <text content="Context: (none)" />}
      {error ? <text content={`Error: ${error}`} /> : null}
      <text content="Press ESC to quit." />
    </box>
  );
};
