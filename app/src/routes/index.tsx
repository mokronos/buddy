import Container from "~/components/Container";
import Sidebar from "~/components/Sidebar";
import Chat from "~/components/Chat";
import MessageBox from "~/components/MessageBox";
import InputBox from "~/components/InputBox";
import { ChatProvider } from "~/context/ChatContext";
import { sampleMessages } from "../data/sampleMessages";

export default function Home() {
  return (
    <ChatProvider messages={sampleMessages}>
        <Container>
          <Sidebar />
          <Chat>
            <MessageBox />
            <InputBox />
          </Chat>
        </Container>
    </ChatProvider>
  );
}
