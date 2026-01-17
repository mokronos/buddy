import { ChatProvider } from "../contexts/ChatContext";
import { ConnectionProvider } from "../contexts/ConnectionContext";
import { SessionProvider } from "../contexts/SessionContext";

export const AppProviders = (props: { children: unknown }) => {
  return (
    <ConnectionProvider>
      <ChatProvider>
        <SessionProvider>{props.children}</SessionProvider>
      </ChatProvider>
    </ConnectionProvider>
  );
};
