import { For, Switch, Match, Show, createEffect, createSignal } from "solid-js";
import AIMessage from "./AIMessage";
import HumanMessage from "./HumanMessage";
import ThinkingMessage from "./ThinkingMessage";
import ToolMessage from "./ToolMessage";
import ToolCallMessage from "./ToolCallMessage";
import WorkingIndicator from "./WorkingIndicator";
import ScrollToBottomButton from "./ScrollToBottomButton";
import { useChat } from "../context/ChatContext";

export default function MessageBox() {
  const { messages, isSending } = useChat();
  let scrollContainerRef: HTMLDivElement | undefined;
  const [isAtBottom, setIsAtBottom] = createSignal(true);

  const scrollBottomThreshold = 32;

  const updateIsAtBottom = () => {
    if (!scrollContainerRef) {
      return;
    }

    const distanceFromBottom =
      scrollContainerRef.scrollHeight -
      scrollContainerRef.scrollTop -
      scrollContainerRef.clientHeight;
    setIsAtBottom(distanceFromBottom <= scrollBottomThreshold);
  };

  const scrollToBottom = () => {
    if (!scrollContainerRef) {
      return;
    }

    scrollContainerRef.scrollTop = scrollContainerRef.scrollHeight;
    setIsAtBottom(true);
  };

  createEffect(() => {
    messages();
    isSending();
    if (isAtBottom()) {
      scrollToBottom();
    }
  });

  const shouldShowWorkingIndicator = () => {
    if (!isSending()) {
      return false;
    }

    const currentMessages = messages();
    const latestMessage = currentMessages[currentMessages.length - 1];
    return latestMessage?.type !== "thinking";
  };

  return (
    <div class="relative flex-1 min-h-0 w-full">
      <div
        ref={scrollContainerRef}
        onScroll={updateIsAtBottom}
        class="h-full min-h-0 w-full border-2 border-slate-700 overflow-y-auto p-4 bg-gray-900"
      >
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
        <Show when={shouldShowWorkingIndicator()}>
          <WorkingIndicator />
        </Show>
      </div>
      <Show when={!isAtBottom()}>
        <ScrollToBottomButton onClick={scrollToBottom} />
      </Show>
    </div>
  );
}
