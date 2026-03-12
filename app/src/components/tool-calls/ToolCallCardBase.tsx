import type { JSX } from "solid-js";

interface ToolCallCardBaseProps {
  toolName: string;
  status?: 'success' | 'error' | 'running' | 'cancelled';
  timestamp?: string;
  children: JSX.Element;
}

function statusIcon(status?: 'success' | 'error' | 'running' | 'cancelled'): string {
  switch (status) {
    case 'success':
      return '✓';
    case 'error':
      return '✗';
    case 'running':
      return '⟳';
    case 'cancelled':
      return '■';
    default:
      return '⚙';
  }
}

export default function ToolCallCardBase(props: ToolCallCardBaseProps) {
  return (
    <div class="mb-4 flex justify-center">
      <div class="card w-full max-w-[92%] border border-info/30 bg-base-100 shadow-md">
        <div class="card-body gap-3 p-4">
          <div class="flex flex-wrap items-center gap-2">
            <span class="badge badge-info badge-sm">Tool Call</span>
            <span class="badge badge-outline badge-sm">{props.toolName}</span>
            <span class="badge badge-ghost badge-sm">{statusIcon(props.status)}</span>
            {props.timestamp ? <span class="text-xs text-base-content/50">{props.timestamp}</span> : null}
          </div>
          {props.children}
        </div>
      </div>
    </div>
  );
}
