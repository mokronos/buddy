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

interface TodoUpdateDiff {
  before: TodoItemView;
  after: TodoItemView;
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

function readTodoUpdateDiff(value: unknown): TodoUpdateDiff | null {
  const record = asRecord(value);
  if (!record) {
    return null;
  }

  const before = readTodoItem(record.before);
  const after = readTodoItem(record.after);
  if (!before || !after) {
    return null;
  }

  return { before, after };
}

function readChangedFields(diff: TodoUpdateDiff): string[] {
  const changes: string[] = [];

  if (diff.before.content !== diff.after.content) {
    changes.push(`Content: "${diff.before.content}" -> "${diff.after.content}"`);
  }

  if (diff.before.status !== diff.after.status) {
    changes.push(`Status: ${statusLabel(diff.before.status)} -> ${statusLabel(diff.after.status)}`);
  }

  if (diff.before.priority !== diff.after.priority) {
    changes.push(`Priority: ${diff.before.priority} -> ${diff.after.priority}`);
  }

  return changes;
}

function priorityClasses(priority: string): string {
  if (priority === "high") {
    return "badge-error";
  }

  if (priority === "low") {
    return "badge-success";
  }

  return "badge-warning";
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
  const updateDiff = readTodoUpdateDiff(props.result);
  const changedFields = updateDiff ? readChangedFields(updateDiff) : [];
  const requestedTodos = readTodos(props.args);
  const resultTodos = readTodos(props.result);
  const paramsText = props.fallbackParamsText || toPrettyText(props.args);
  const resultText = props.fallbackResultText || toPrettyText(props.result);

  return (
    <ToolCallCardBase toolName={props.toolName} status={props.status} timestamp={props.timestamp}>
      <Show when={props.toolName === "todoupdate" && updateDiff !== null}>
        <div class="mb-3 rounded-box border border-accent/20 bg-accent/10 px-3 py-2">
          <div class="mb-1 text-xs text-accent">Updated todo: {updateDiff!.after.id}</div>
          <Show when={changedFields.length > 0} fallback={<div class="text-xs text-base-content/70">No field changes detected.</div>}>
            <ul class="space-y-1 text-xs text-base-content/80">
              <For each={changedFields}>{(change) => <li>{change}</li>}</For>
            </ul>
          </Show>
        </div>
      </Show>

      <Show when={requestedTodos.length > 0}>
        <div class="mb-2 text-xs text-info">Requested todos: {requestedTodos.length}</div>
        <div class="mb-3 space-y-2">
          <For each={requestedTodos}>
            {(todo) => (
              <div class="rounded-box border border-base-300 bg-base-200 px-3 py-2">
                <div class="text-sm">{todo.content}</div>
                <div class="mt-1 flex items-center gap-2">
                  <span class={`w-2 h-2 rounded-full ${statusDot(todo.status)}`} />
                  <span class="text-xs capitalize text-base-content/70">{statusLabel(todo.status)}</span>
                  <span class={`badge badge-sm ${priorityClasses(todo.priority)}`}>
                    {todo.priority}
                  </span>
                </div>
              </div>
            )}
          </For>
        </div>
      </Show>

      <Show when={resultTodos.length > 0}>
        <div class="mb-2 text-xs text-info">Current todo list: {resultTodos.length}</div>
        <div class="mb-2 space-y-2">
          <For each={resultTodos}>
            {(todo) => (
              <div class="rounded-box border border-base-300 bg-base-200 px-3 py-2">
                <div class="text-sm">{todo.content}</div>
                <div class="mt-1 flex items-center gap-2">
                  <span class={`w-2 h-2 rounded-full ${statusDot(todo.status)}`} />
                  <span class="text-xs capitalize text-base-content/70">{statusLabel(todo.status)}</span>
                  <span class={`badge badge-sm ${priorityClasses(todo.priority)}`}>
                    {todo.priority}
                  </span>
                  <Show when={todo.id.length > 0}>
                    <span class="text-[10px] text-base-content/40">#{todo.id}</span>
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
