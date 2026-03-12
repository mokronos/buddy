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
    <div class="border-t border-base-300 bg-base-100/80 p-4">
      <PromptSuggestions
        onSelect={(prompt) => {
          setInputValue(prompt);
          textareaRef?.focus();
        }}
      />
      <form ref={formRef} onSubmit={handleSubmit} class="flex gap-2">
        <textarea
          ref={textareaRef}
          class="textarea textarea-primary flex-1 resize-none bg-base-200"
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
          class="btn btn-primary self-end"
          disabled={!inputValue().trim() || isSending()}
        >
          {isSending() ? <span class="loading loading-spinner loading-sm" /> : null}
          {isSending() ? "Sending" : "Send"}
        </button>
      </form>
    </div>
  );
}
