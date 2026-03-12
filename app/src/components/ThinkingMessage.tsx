interface ThinkingMessageProps {
  content: string;
  timestamp?: string;
}

export default function ThinkingMessage(props: ThinkingMessageProps) {
  return (
    <div class="mb-4 flex justify-start">
      <div class="card max-w-[85%] border border-accent/30 bg-accent/10 shadow-sm">
        <div class="card-body gap-2 p-4">
          <div class="flex items-center gap-2">
            <span class="badge badge-accent badge-sm">Thinking</span>
            {props.timestamp ? <span class="text-xs text-base-content/50">{props.timestamp}</span> : null}
          </div>
          <div class="whitespace-pre-wrap text-sm leading-6 text-base-content/80">{props.content}</div>
        </div>
      </div>
    </div>
  );
}
