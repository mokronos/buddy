import { For, Switch, Match, createEffect } from "solid-js";
import AIMessage from "./AIMessage";
import HumanMessage from "./HumanMessage";
import ThinkingMessage from "./ThinkingMessage";
import ToolMessage from "./ToolMessage";
import ToolCallMessage from "./ToolCallMessage";
import { useChat } from "../context/ChatContext";

export default function MessageBox() {
    const { messages } = useChat();
    let scrollContainerRef: HTMLDivElement | undefined;

    // Auto-scroll to bottom when messages change
    createEffect(() => {
        messages(); // Track messages changes
        if (scrollContainerRef) {
            scrollContainerRef.scrollTop = scrollContainerRef.scrollHeight;
        }
    });

  return (
    <div ref={scrollContainerRef} class="flex-1 w-full border-2 border-slate-700 overflow-y-auto p-4 bg-gray-900">
      <For each={messages()}>
        {(message) => (
          <Switch fallback={null}>
            <Match when={message.type === 'ai'}>
              <AIMessage
                content={message.content}
                timestamp={message.timestamp}
              />
            </Match>
            <Match when={message.type === 'human'}>
              <HumanMessage
                content={message.content}
                timestamp={message.timestamp}
              />
            </Match>
            <Match when={message.type === 'thinking'}>
              <ThinkingMessage
                content={message.content}
                timestamp={message.timestamp}
              />
            </Match>
            <Match when={message.type === 'tool'}>
              <ToolMessage
                toolName={message.toolName!}
                content={message.content}
                status={message.toolStatus}
                timestamp={message.timestamp}
              />
            </Match>
            <Match when={message.type === 'tool-call'}>
              <ToolCallMessage
                toolName={message.toolName || "Unknown Tool"}
                status={message.toolStatus}
                toolCallId={message.toolCallId}
                toolCallArgs={message.toolCallArgs}
                toolResultData={message.toolResultData}
                toolCallParams={message.toolCallParams}
                toolResult={message.toolResult || message.content}
                timestamp={message.timestamp}
              />
            </Match>
          </Switch>
        )}
      </For>
    </div>
  );
}
