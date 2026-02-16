import { For, Show } from "solid-js";
import ExpandableTextBlock from "./ExpandableTextBlock";
import { asRecord, toPrettyText } from "./format";
import ToolCallCardBase from "./ToolCallCardBase";
import type { ToolCallRendererProps } from "./types";

interface TodoItemView {
  id: string;
  content: string;
  status: string;
  priority: string;
}

function readTodoItem(value: unknown): TodoItemView | null {
  const record = asRecord(value);
  if (!record) {
    return null;
  }

  const id = typeof record.id === "string" ? record.id : "";
  const content = typeof record.content === "string" ? record.content : "";
  const status = typeof record.status === "string" ? record.status : "pending";
  const priority = typeof record.priority === "string" ? record.priority : "medium";

  if (content.length === 0) {
    return null;
  }

  return {
    id,
    content,
    status,
    priority,
  };
}

function readTodos(value: unknown): TodoItemView[] {
  if (!value) {
    return [];
  }

  if (Array.isArray(value)) {
    return value.map(readTodoItem).filter((item): item is TodoItemView => item !== null);
  }

  const record = asRecord(value);
  if (!record) {
    return [];
  }

  const todos = record.todos;
  if (!Array.isArray(todos)) {
    return [];
  }

  return todos.map(readTodoItem).filter((item): item is TodoItemView => item !== null);
}

function priorityClasses(priority: string): string {
  if (priority === "high") {
    return "bg-rose-900 text-rose-200 border-rose-700";
  }

  if (priority === "low") {
    return "bg-emerald-900 text-emerald-200 border-emerald-700";
  }

  return "bg-amber-900 text-amber-200 border-amber-700";
}

function statusDot(status: string): string {
  if (status === "completed") {
    return "bg-emerald-400";
  }

  if (status === "in_progress") {
    return "bg-amber-400";
  }

  if (status === "cancelled") {
    return "bg-rose-400";
  }

  return "bg-slate-400";
}

function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

export default function TodoToolCallRenderer(props: ToolCallRendererProps) {
  const requestedTodos = readTodos(props.args);
  const resultTodos = readTodos(props.result);
  const paramsText = props.fallbackParamsText || toPrettyText(props.args);
  const resultText = props.fallbackResultText || toPrettyText(props.result);

  return (
    <ToolCallCardBase toolName={props.toolName} status={props.status} timestamp={props.timestamp}>
      <Show when={requestedTodos.length > 0}>
        <div class="text-xs text-cyan-300 mb-2">Requested todos: {requestedTodos.length}</div>
        <div class="mb-3 space-y-2">
          <For each={requestedTodos}>
            {(todo) => (
              <div class="border border-slate-700 bg-slate-900 rounded px-3 py-2">
                <div class="text-sm text-slate-100">{todo.content}</div>
                <div class="mt-1 flex items-center gap-2">
                  <span class={`w-2 h-2 rounded-full ${statusDot(todo.status)}`} />
                  <span class="text-xs text-slate-300 capitalize">{statusLabel(todo.status)}</span>
                  <span class={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded border ${priorityClasses(todo.priority)}`}>
                    {todo.priority}
                  </span>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>

      <Show when={resultTodos.length > 0}>
        <div class="text-xs text-cyan-300 mb-2">Current todo list: {resultTodos.length}</div>
        <div class="mb-2 space-y-2">
          <For each={resultTodos}>
            {(todo) => (
              <div class="border border-slate-700 bg-slate-900 rounded px-3 py-2">
                <div class="text-sm text-slate-100">{todo.content}</div>
                <div class="mt-1 flex items-center gap-2">
                  <span class={`w-2 h-2 rounded-full ${statusDot(todo.status)}`} />
                  <span class="text-xs text-slate-300 capitalize">{statusLabel(todo.status)}</span>
                  <span class={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded border ${priorityClasses(todo.priority)}`}>
                    {todo.priority}
                  </span>
                  <Show when={todo.id.length > 0}>
                    <span class="text-[10px] text-slate-500">#{todo.id}</span>
                  </Show>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>

      <Show when={requestedTodos.length === 0 && paramsText.length > 0}>
        <ExpandableTextBlock title="Todo Input" content={paramsText} compact />
      </Show>
      <Show when={resultTodos.length === 0}>
        <ExpandableTextBlock title="Todo Result" content={resultText} />
      </Show>
    </ToolCallCardBase>
  );
}
