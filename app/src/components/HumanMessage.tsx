import MarkdownContent from "./MarkdownContent";

interface HumanMessageProps {
  content: string;
  timestamp?: string;
}

export default function HumanMessage(props: HumanMessageProps) {
  return (
    <div class="mb-4 flex justify-end">
      <div class="card max-w-[85%] border border-primary/30 bg-primary/12 shadow-md">
        <div class="card-body gap-2 p-4">
          <div class="flex items-center justify-end gap-2">
            {props.timestamp ? <span class="text-xs text-base-content/50">{props.timestamp}</span> : null}
            <span class="badge badge-primary badge-sm">You</span>
          </div>
          <div class="text-sm leading-6 text-base-content">
            <MarkdownContent content={props.content} />
          </div>
        </div>
      </div>
    </div>
  );
}
