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
        <div data-theme="night" class="min-h-screen bg-base-300 text-base-content">
          <QueryClientProvider client={queryClient}>
            <AgentsProvider>
              <ChatProvider messages={[]}>
                <Suspense
                  fallback={
                    <main class="flex min-h-screen flex-col">
                      <TopTabs />
                      <div class="min-h-0 flex-1 px-4 py-4 lg:px-6">
                        <div class="mx-auto flex w-full max-w-7xl flex-col gap-4">
                          <Skeleton class="h-16 w-full rounded-box" />
                          <Skeleton class="h-32 w-full rounded-box" />
                          <Skeleton class="h-32 w-full rounded-box" />
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
        </div>
      )}
    >
      <FileRoutes />
    </Router>
  );
}
