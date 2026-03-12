import MarkdownContent from "./MarkdownContent";

interface AIMessageProps {
  content: string;
  timestamp?: string;
  streaming?: boolean;
}

export default function AIMessage(props: AIMessageProps) {
  return (
    <div class="mb-4 flex justify-start">
      <div class="card max-w-[85%] border border-info/30 bg-base-100 shadow-md">
        <div class="card-body gap-2 p-4">
          <div class="flex items-center gap-2">
            <span class="badge badge-info badge-sm">Assistant</span>
            {props.streaming ? <span class="badge badge-outline badge-sm">streaming</span> : null}
            {props.timestamp ? <span class="text-xs text-base-content/50">{props.timestamp}</span> : null}
          </div>
          <div class="text-sm leading-6 text-base-content">
            {props.streaming ? <div class="whitespace-pre-wrap break-words">{props.content}</div> : <MarkdownContent content={props.content} />}
          </div>
        </div>
      </div>
    </div>
  );
}
