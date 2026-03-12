interface PromptSuggestionsProps {
  onSelect: (prompt: string) => void;
}

const QUICK_PROMPTS = [
  "add some random items to your todo list",
  "show me my todo list",
  "add 3 todos with ids todo-1, todo-2, todo-3",
  "update todo-2 status to completed and priority to high",
  "rename todo-1 to 'Buy groceries and snacks'",
  "delete todo-3 from my todo list",
  "replace my todo list with two fresh tasks",
  "find the latest AI news and summarize it",
  "fetch https://example.com and give me a short summary",
  "what tools do you have available",
  "give me a 5 paragraph poem about your life",
];

export default function PromptSuggestions(props: PromptSuggestionsProps) {
  return (
    <div class="mb-3">
      <div class="mb-2 text-xs uppercase tracking-[0.2em] text-base-content/50">Quick prompts</div>
      <div class="flex flex-wrap gap-2">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            type="button"
            class="badge badge-outline badge-lg h-auto max-w-full whitespace-normal px-3 py-3 text-left text-[11px] leading-4 hover:border-primary hover:text-primary"
            onClick={() => props.onSelect(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
