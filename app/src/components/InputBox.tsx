import { createSignal } from "solid-js";
import { useChat } from "../context/ChatContext";

export default function InputBox() {
  const [messages, setMessages] = useChat();
  const [inputValue, setInputValue] = createSignal("");

  const handleSubmit = (e: Event) => {
    e.preventDefault();
    const message = inputValue().trim();
    if (message) {
      const newMessage = {
        id: Date.now().toString(),
        type: 'human' as const,
        content: message,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages([...messages(), newMessage]);
      setInputValue("");
    }
  };

  return (
    <div class="w-full border-2 border-slate-700 p-6">
      <form onSubmit={handleSubmit} class="flex gap-2">
        <textarea
          class="textarea flex-1 resize-none"
          placeholder="Type your message here..."
          value={inputValue()}
          onInput={(e) => setInputValue(e.currentTarget.value)}
          rows="3"
        />
        <button
          type="submit"
          class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          disabled={!inputValue().trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
}
