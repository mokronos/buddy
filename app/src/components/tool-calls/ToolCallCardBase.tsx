import type { JSX } from "solid-js";

interface ToolCallCardBaseProps {
  toolName: string;
  status?: 'success' | 'error' | 'running';
  timestamp?: string;
  children: JSX.Element;
}

function statusIcon(status?: 'success' | 'error' | 'running'): string {
  switch (status) {
    case 'success':
      return '✓';
    case 'error':
      return '✗';
    case 'running':
      return '⟳';
    default:
      return '⚙';
  }
}

export default function ToolCallCardBase(props: ToolCallCardBaseProps) {
  return (
    <div class="flex justify-center mb-4">
      <div class="border border-cyan-600 bg-slate-800 rounded-lg p-3 max-w-[90%] w-full">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-6 h-6 bg-cyan-700 rounded-full flex items-center justify-center">
            <span class="text-white text-xs">{statusIcon(props.status)}</span>
          </div>
          <span class="text-sm font-medium text-cyan-200">Tool Call</span>
          <span class="text-sm text-gray-300">{props.toolName}</span>
          {props.timestamp && <span class="text-xs text-gray-400">{props.timestamp}</span>}
        </div>
        {props.children}
      </div>
    </div>
  );
}
