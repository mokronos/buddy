interface ToolMessageProps {
  toolName: string;
  content: string;
  status?: 'success' | 'error' | 'running';
  timestamp?: string;
}

export default function ToolMessage(props: ToolMessageProps) {
  const getStatusColor = () => {
    switch (props.status) {
      case 'success': return 'bg-slate-700 border-purple-500';
      case 'error': return 'bg-red-900 border-red-500';
      case 'running': return 'bg-yellow-900 border-yellow-500';
      default: return 'bg-slate-700 border-slate-500';
    }
  };

  const getStatusIcon = () => {
    switch (props.status) {
      case 'success': return '✓';
      case 'error': return '✗';
      case 'running': return '⟳';
      default: return '⚙';
    }
  };

  return (
    <div class="flex justify-center mb-4">
      <div class={`border rounded-lg p-3 max-w-[90%] ${getStatusColor()}`}>
        <div class="flex items-center gap-2 mb-2">
          <div class="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center">
            <span class="text-white text-xs">{getStatusIcon()}</span>
          </div>
          <span class="text-sm font-medium text-gray-200">{props.toolName}</span>
          {props.timestamp && (
            <span class="text-xs text-gray-400">{props.timestamp}</span>
          )}
        </div>
        <div class="text-gray-200 text-sm whitespace-pre-wrap bg-slate-800 p-2 rounded">
          {props.content}
        </div>
      </div>
    </div>
  );
}