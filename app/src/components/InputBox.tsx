import { createSignal } from "solid-js";
import PromptSuggestions from "./PromptSuggestions";
import { useChat } from "../context/ChatContext";

export default function InputBox() {
  const { sendMessage, isSending } = useChat();
  const [inputValue, setInputValue] = createSignal("");
  let formRef: HTMLFormElement | undefined;
  let textareaRef: HTMLTextAreaElement | undefined;

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    const message = inputValue().trim();
    if (message) {
      await sendMessage(message);
      setInputValue("");
    }
  };

  return (
    <div class="w-full border-2 border-slate-700 p-6">
      <PromptSuggestions
        onSelect={(prompt) => {
          setInputValue(prompt);
          textareaRef?.focus();
        }}
      />
      <form ref={formRef} onSubmit={handleSubmit} class="flex gap-2">
        <textarea
          ref={textareaRef}
          class="textarea flex-1 resize-none"
          placeholder="Type your message here..."
          value={inputValue()}
          onInput={(e) => setInputValue(e.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
              e.preventDefault();
              formRef?.requestSubmit();
            }
          }}
          rows="3"
        />
        <button
          type="submit"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          disabled={!inputValue().trim() || isSending()}
        >
          {isSending() ? "Sending..." : "Send"}
        </button>
      </form>
    </div>
  );
}
