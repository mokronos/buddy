import type { Component } from "solid-js";
import DefaultToolCallRenderer from "./DefaultToolCallRenderer";
import TodoToolCallRenderer from "./TodoToolCallRenderer";
import type { ToolCallRendererProps } from "./types";
import WebSearchToolCallRenderer from "./WebSearchToolCallRenderer";

type ToolCallRendererComponent = Component<ToolCallRendererProps>;

function normalizeToolName(toolName: string): string {
  return toolName.toLowerCase().trim().replace(/[-\s]/g, "_");
}

const toolRenderers: Record<string, ToolCallRendererComponent> = {
  todowrite: TodoToolCallRenderer,
  todoread: TodoToolCallRenderer,
  todoadd: TodoToolCallRenderer,
  todoupdate: TodoToolCallRenderer,
  tododelete: TodoToolCallRenderer,
  web_search: WebSearchToolCallRenderer,
  fetch_web_page: WebSearchToolCallRenderer,
};

export function getToolCallRenderer(toolName: string): ToolCallRendererComponent {
  const normalizedToolName = normalizeToolName(toolName);
  return toolRenderers[normalizedToolName] || DefaultToolCallRenderer;
}
