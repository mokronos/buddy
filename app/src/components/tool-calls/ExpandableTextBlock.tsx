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
      <div class="text-xs uppercase tracking-wide text-gray-400 mb-1">{props.title}</div>
      <pre class={`text-gray-200 whitespace-pre-wrap bg-slate-900 p-2 rounded overflow-x-auto ${props.compact ? "text-xs" : "text-sm"}`}>
        {shownText()}
      </pre>
      <Show when={canExpand()}>
        <button
          type="button"
          class="mt-2 text-xs text-cyan-300 hover:text-cyan-200"
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded() ? "Show less" : "Show more"}
        </button>
      </Show>
    </div>
  );
}
