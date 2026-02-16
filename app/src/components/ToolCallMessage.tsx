import { getToolCallRenderer } from "./tool-calls/registry";

interface ToolCallMessageProps {
  toolName: string;
  status?: 'success' | 'error' | 'running';
  toolCallParams?: string;
  toolCallId?: string;
  toolCallArgs?: unknown;
  toolResultData?: unknown;
  toolResult: string;
  timestamp?: string;
}

export default function ToolCallMessage(props: ToolCallMessageProps) {
  const Renderer = getToolCallRenderer(props.toolName);

  return <Renderer
    toolName={props.toolName}
    status={props.status}
    timestamp={props.timestamp}
    toolCallId={props.toolCallId}
    args={props.toolCallArgs}
    result={props.toolResultData}
    fallbackParamsText={props.toolCallParams}
    fallbackResultText={props.toolResult}
  />;
}
