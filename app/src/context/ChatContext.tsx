import { createContext, createSignal, useContext, type JSX } from "solid-js";
import { createClient } from "~/buddy-client/client";

const ChatContext = createContext<[() => any[], (messages: any[]) => void]>();

export function ChatProvider (props : { children: JSX.Element, messages: any[] }) {

    const [messages, setMessages] = createSignal(props.messages || []);

    const buddyClient = createClient()
    

    return (
        <ChatContext.Provider value={[messages, setMessages]}>
            {props.children}
        </ChatContext.Provider>
    );
}

export function useChat () { return useContext(ChatContext)!; }
