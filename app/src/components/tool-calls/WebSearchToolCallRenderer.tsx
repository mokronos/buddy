import { Show } from "solid-js";
import ExpandableTextBlock from "./ExpandableTextBlock";
import { asRecord, toPrettyText } from "./format";
import ToolCallCardBase from "./ToolCallCardBase";
import type { ToolCallRendererProps } from "./types";

function readQuery(args: unknown): string | null {
  const record = asRecord(args);
  if (!record) {
    return null;
  }

  const candidates = [record.query, record.q, record.text, record.url];
  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim().length > 0) {
      return candidate;
    }
  }

  return null;
}

export default function WebSearchToolCallRenderer(props: ToolCallRendererProps) {
  const paramsText = props.fallbackParamsText || toPrettyText(props.args);
  const resultText = props.fallbackResultText || toPrettyText(props.result);
  const query = readQuery(props.args);

  return (
    <ToolCallCardBase toolName={props.toolName} status={props.status} timestamp={props.timestamp}>
      <Show when={query}>
        <div class="mb-2 flex items-center gap-2">
          <span class="badge badge-primary badge-outline">Query</span>
          <span class="text-sm">{query}</span>
        </div>
      </Show>
      <Show when={paramsText.length > 0}>
        <ExpandableTextBlock title="Search Input" content={paramsText} compact />
      </Show>
      <ExpandableTextBlock title="Search Result" content={resultText} />
    </ToolCallCardBase>
  );
}
