import Container from "~/components/Container";
import Sidebar from "~/components/Sidebar";
import Chat from "~/components/Chat";
import MessageBox from "~/components/MessageBox";
import InputBox from "~/components/InputBox";
import TopTabs from "~/components/TopTabs";
import TaskTabs from "~/components/TaskTabs";

export default function Home() {
  return (
    <div class="flex h-screen flex-col">
      <TopTabs />
      <Container>
        <Sidebar />
        <Chat>
          <TaskTabs />
          <MessageBox />
          <InputBox />
        </Chat>
      </Container>
    </div>
  );
}
