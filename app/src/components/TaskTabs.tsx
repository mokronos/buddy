import { useChat } from "~/context/ChatContext";

export default function TaskTabs() {
  const { tasks, activeTaskId, setActiveTaskId, createTask } = useChat();

  return (
    <div class="flex items-center gap-2 overflow-x-auto border-b border-zinc-800 bg-zinc-950 px-3 py-2">
      {tasks().map((task) => {
        const isActive = task.id === activeTaskId();
        return (
          <button
            type="button"
            onClick={() => setActiveTaskId(task.id)}
            class={`inline-flex items-center gap-2 whitespace-nowrap rounded-md border px-3 py-1 text-xs transition-colors ${
              isActive
                ? "border-cyan-500 bg-cyan-950/50 text-cyan-100"
                : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:border-zinc-500"
            }`}
          >
            <span>{task.label}</span>
            {task.isSending ? <span class="inline-block h-2 w-2 rounded-full bg-cyan-400" /> : null}
          </button>
        );
      })}
      <button
        type="button"
        onClick={createTask}
        class="inline-flex items-center whitespace-nowrap rounded-md border border-zinc-700 px-3 py-1 text-xs text-zinc-200 hover:border-zinc-500"
      >
        + New Task
      </button>
    </div>
  );
}
