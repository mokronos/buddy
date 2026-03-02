import { Router } from "@solidjs/router";
import { QueryClient, QueryClientProvider } from "@tanstack/solid-query";
import { FileRoutes } from "@solidjs/start/router";
import { Suspense } from "solid-js";
import TopTabs from "~/components/TopTabs";
import Skeleton from "~/components/ui/Skeleton";
import { AgentsProvider } from "~/context/AgentsContext";
import { ChatProvider } from "~/context/ChatContext";
import "./app.css";

export default function App() {
  const queryClient = new QueryClient();

  return (
    <Router
      root={props => (
        <QueryClientProvider client={queryClient}>
          <AgentsProvider>
            <ChatProvider messages={[]}>
              <Suspense
                fallback={
                  <main class="flex h-screen flex-col bg-zinc-950 text-zinc-100">
                    <TopTabs />
                    <div class="min-h-0 flex-1 overflow-y-auto px-6 py-6">
                      <div class="mx-auto flex w-full max-w-7xl flex-col gap-4">
                        <Skeleton class="h-8 w-44" />
                        <Skeleton class="h-24 w-full" />
                        <Skeleton class="h-24 w-full" />
                      </div>
                    </div>
                  </main>
                }
              >
                {props.children}
              </Suspense>
            </ChatProvider>
          </AgentsProvider>
        </QueryClientProvider>
      )}
    >
      <FileRoutes />
    </Router>
  );
}
