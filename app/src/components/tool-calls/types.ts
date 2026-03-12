export interface ToolCallRendererProps {
  toolName: string;
  status?: 'success' | 'error' | 'running' | 'cancelled';
  timestamp?: string;
  toolCallId?: string;
  args?: unknown;
  result?: unknown;
  fallbackParamsText?: string;
  fallbackResultText?: string;
}
