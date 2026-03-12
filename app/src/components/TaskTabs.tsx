import { useChat } from "~/context/ChatContext";

export default function TaskTabs() {
  const { tasks, activeTaskId, setActiveTaskId, createTask } = useChat();

  return (
    <div class="border-b border-base-300 px-4 py-3">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="tabs tabs-boxed bg-base-200">
          {tasks().map((task) => {
            const isActive = task.id === activeTaskId();
            return (
              <button type="button" onClick={() => setActiveTaskId(task.id)} class={`tab gap-2 ${isActive ? "tab-active" : ""}`}>
                <span>{task.label}</span>
                {task.isSending ? <span class="badge badge-primary badge-xs" /> : null}
              </button>
            );
          })}
        </div>
        <button type="button" onClick={createTask} class="btn btn-sm btn-outline btn-primary">
          New Task
        </button>
      </div>
    </div>
  );
}
