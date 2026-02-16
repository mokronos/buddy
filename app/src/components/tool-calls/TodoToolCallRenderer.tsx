import { Show } from "solid-js";
import ExpandableTextBlock from "./ExpandableTextBlock";
import { asRecord, toPrettyText } from "./format";
import ToolCallCardBase from "./ToolCallCardBase";
import type { ToolCallRendererProps } from "./types";

function getTodoCount(value: unknown): number | null {
  const record = asRecord(value);
  if (!record) {
    return null;
  }

  const todos = record.todos;
  if (!Array.isArray(todos)) {
    return null;
  }

  return todos.length;
}

export default function TodoToolCallRenderer(props: ToolCallRendererProps) {
  const paramsText = props.fallbackParamsText || toPrettyText(props.args);
  const resultText = props.fallbackResultText || toPrettyText(props.result);
  const todoCount = getTodoCount(props.args);

  return (
    <ToolCallCardBase toolName={props.toolName} status={props.status} timestamp={props.timestamp}>
      <Show when={todoCount !== null}>
        <div class="text-xs text-cyan-300 mb-2">Todos in request: {todoCount}</div>
      </Show>
      <Show when={paramsText.length > 0}>
        <ExpandableTextBlock title="Todo Input" content={paramsText} compact />
      </Show>
      <ExpandableTextBlock title="Todo Result" content={resultText} />
    </ToolCallCardBase>
  );
}
