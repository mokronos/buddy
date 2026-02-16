interface PromptSuggestionsProps {
  onSelect: (prompt: string) => void;
}

const QUICK_PROMPTS = [
  "add some random items to your todo list",
  "show me my todo list",
  "find the latest AI news and summarize it",
  "fetch https://example.com and give me a short summary",
];

export default function PromptSuggestions(props: PromptSuggestionsProps) {
  return (
    <div class="mb-3">
      <div class="text-xs text-slate-400 mb-2">Quick prompts</div>
      <div class="flex flex-wrap gap-2">
        {QUICK_PROMPTS.map((prompt) => (
          <button
            type="button"
            class="text-xs px-3 py-1 rounded-full border border-slate-600 text-slate-200 hover:bg-slate-700"
            onClick={() => props.onSelect(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
