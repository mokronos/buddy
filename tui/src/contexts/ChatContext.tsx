import { createContext, createSignal, useContext } from "solid-js";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "status";
  content: string;
  streaming?: boolean;
};

export type ChatContextValue = {
  messages: () => ChatMessage[];
  appendMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updater: (message: ChatMessage) => ChatMessage) => void;
  replaceMessages: (messages: ChatMessage[]) => void;
};

const ChatContext = createContext<ChatContextValue>();

export const ChatProvider = (props: { children: unknown }) => {
  const [messages, setMessages] = createSignal<ChatMessage[]>([]);

  const appendMessage = (message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  };

  const updateMessage = (id: string, updater: (message: ChatMessage) => ChatMessage) => {
    setMessages((prev) => prev.map((message) => (message.id === id ? updater(message) : message)));
  };

  const replaceMessages = (next: ChatMessage[]) => {
    setMessages(next);
  };

  const value: ChatContextValue = {
    messages,
    appendMessage,
    updateMessage,
    replaceMessages,
  };

  return <ChatContext.Provider value={value}>{props.children}</ChatContext.Provider>;
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within ChatProvider");
  }
  return context;
};
