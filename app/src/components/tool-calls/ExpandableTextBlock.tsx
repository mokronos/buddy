import { Show, createMemo, createSignal } from "solid-js";

interface ExpandableTextBlockProps {
  title: string;
  content: string;
  compact?: boolean;
  maxLength?: number;
}

const DEFAULT_MAX_LENGTH = 500;

export default function ExpandableTextBlock(props: ExpandableTextBlockProps) {
  const [expanded, setExpanded] = createSignal(false);

  const canExpand = createMemo(() => {
    const maxLength = props.maxLength ?? DEFAULT_MAX_LENGTH;
    return props.content.length > maxLength;
  });

  const shownText = createMemo(() => {
    if (expanded() || !canExpand()) {
      return props.content;
    }

    const maxLength = props.maxLength ?? DEFAULT_MAX_LENGTH;
    return `${props.content.slice(0, maxLength)}...`;
  });

  return (
    <div class="mb-2">
      <div class="mb-1 text-xs uppercase tracking-[0.2em] text-base-content/50">{props.title}</div>
      <pre class={`overflow-x-auto whitespace-pre-wrap rounded-box bg-base-200 p-3 ${props.compact ? "text-xs" : "text-sm"}`}>
        {shownText()}
      </pre>
      <Show when={canExpand()}>
        <button
          type="button"
          class="btn btn-ghost btn-xs mt-2"
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded() ? "Show less" : "Show more"}
        </button>
      </Show>
    </div>
  );
}
