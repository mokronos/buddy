interface ToolMessageProps {
  toolName: string;
  content: string;
  status?: 'success' | 'error' | 'running' | 'cancelled';
  timestamp?: string;
}

export default function ToolMessage(props: ToolMessageProps) {
  const alertClass = () => {
    switch (props.status) {
      case 'success':
        return 'alert-success';
      case 'error':
        return 'alert-error';
      case 'running':
        return 'alert-warning';
      case 'cancelled':
        return 'alert-warning';
      default:
        return 'alert-info';
    }
  };

  const statusLabel = () => {
    switch (props.status) {
      case 'success':
        return 'completed';
      case 'error':
        return 'failed';
      case 'running':
        return 'running';
      case 'cancelled':
        return 'canceled';
      default:
        return 'notice';
    }
  };

  return (
    <div class="mb-4 flex justify-center">
      <div class={`alert max-w-[92%] items-start shadow-md ${alertClass()}`}>
        <div class="flex w-full flex-col gap-2">
          <div class="flex flex-wrap items-center gap-2">
            <span class="badge badge-neutral badge-sm uppercase">{props.toolName}</span>
            <span class="badge badge-outline badge-sm">{statusLabel()}</span>
            {props.timestamp ? <span class="text-xs opacity-70">{props.timestamp}</span> : null}
          </div>
          <div class="rounded-box bg-base-300/60 p-3 text-sm whitespace-pre-wrap">{props.content}</div>
        </div>
      </div>
    </div>
  );
}
