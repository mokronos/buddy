import { Show } from "solid-js";
import ExpandableTextBlock from "./ExpandableTextBlock";
import { toPrettyText } from "./format";
import ToolCallCardBase from "./ToolCallCardBase";
import type { ToolCallRendererProps } from "./types";

export default function DefaultToolCallRenderer(props: ToolCallRendererProps) {
  const paramsText = props.fallbackParamsText || toPrettyText(props.args);
  const resultText = props.fallbackResultText || toPrettyText(props.result);

  return (
    <ToolCallCardBase toolName={props.toolName} status={props.status} timestamp={props.timestamp}>
      <Show when={paramsText.length > 0}>
        <ExpandableTextBlock title="Params" content={paramsText} compact />
      </Show>
      <ExpandableTextBlock title="Result" content={resultText} />
    </ToolCallCardBase>
  );
}
