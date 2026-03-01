import Container from "~/components/Container";
import Sidebar from "~/components/Sidebar";
import Chat from "~/components/Chat";
import MessageBox from "~/components/MessageBox";
import InputBox from "~/components/InputBox";
import TopTabs from "~/components/TopTabs";
import { ChatProvider } from "~/context/ChatContext";

export default function Home() {
  return (
    <ChatProvider messages={[]}>
      <div class="flex h-screen flex-col">
        <TopTabs />
        <Container>
          <Sidebar />
          <Chat>
            <MessageBox />
            <InputBox />
          </Chat>
        </Container>
      </div>
    </ChatProvider>
  );
}
