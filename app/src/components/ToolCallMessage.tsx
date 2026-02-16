import { Show, createMemo, createSignal } from "solid-js";

interface ToolCallMessageProps {
  toolName: string;
  toolCallParams?: string;
  toolResult: string;
  timestamp?: string;
}

const MAX_PREVIEW_LENGTH = 500;

export default function ToolCallMessage(props: ToolCallMessageProps) {
  const [isExpanded, setIsExpanded] = createSignal(false);

  const canExpand = createMemo(() => props.toolResult.length > MAX_PREVIEW_LENGTH);

  const displayedResult = createMemo(() => {
    if (isExpanded() || !canExpand()) {
      return props.toolResult;
    }

    return `${props.toolResult.slice(0, MAX_PREVIEW_LENGTH)}...`;
  });

  return (
    <div class="flex justify-center mb-4">
      <div class="border border-cyan-600 bg-slate-800 rounded-lg p-3 max-w-[90%] w-full">
        <div class="flex items-center gap-2 mb-2">
          <div class="w-6 h-6 bg-cyan-700 rounded-full flex items-center justify-center">
            <span class="text-white text-xs">⚙</span>
          </div>
          <span class="text-sm font-medium text-cyan-200">Tool Call</span>
          <span class="text-sm text-gray-300">{props.toolName}</span>
          <Show when={props.timestamp}>
            <span class="text-xs text-gray-400">{props.timestamp}</span>
          </Show>
        </div>

        <Show when={props.toolCallParams && props.toolCallParams!.length > 0}>
          <div class="mb-2">
            <div class="text-xs uppercase tracking-wide text-gray-400 mb-1">Params</div>
            <pre class="text-gray-200 text-xs whitespace-pre-wrap bg-slate-900 p-2 rounded overflow-x-auto">
              {props.toolCallParams}
            </pre>
          </div>
        </Show>

        <div>
          <div class="text-xs uppercase tracking-wide text-gray-400 mb-1">Result</div>
          <pre class="text-gray-200 text-sm whitespace-pre-wrap bg-slate-900 p-2 rounded overflow-x-auto">
            {displayedResult()}
          </pre>
        </div>

        <Show when={canExpand()}>
          <button
            type="button"
            class="mt-2 text-xs text-cyan-300 hover:text-cyan-200"
            onClick={() => setIsExpanded((current) => !current)}
          >
            {isExpanded() ? "Show less" : "Show more"}
          </button>
        </Show>
      </div>
    </div>
  );
}
