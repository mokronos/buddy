import { createContext, createSignal, useContext, type JSX } from "solid-js";

const ChatContext = createContext<[() => any[], (messages: any[]) => void]>();

export function ChatProvider (props : { children: JSX.Element, messages: any[] }) {

    const [messages, setMessages] = createSignal(props.messages || []);

    return (
        <ChatContext.Provider value={[messages, setMessages]}>
            {props.children}
        </ChatContext.Provider>
    );
}

export function useChat () { return useContext(ChatContext)!; }
