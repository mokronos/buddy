import { onMount } from "solid-js";
import Container from "~/components/Container";
import Sidebar from "~/components/Sidebar";
import Chat from "~/components/Chat";
import MessageBox from "~/components/MessageBox";
import InputBox from "~/components/InputBox";
import TopTabs from "~/components/TopTabs";
import TaskTabs from "~/components/TaskTabs";
import { useAgents } from "~/context/AgentsContext";

export default function Home() {
  const { refreshAgents } = useAgents();

  onMount(() => {
    void refreshAgents();
  });

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
