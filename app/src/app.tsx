import { Router } from "@solidjs/router";
import { QueryClient, QueryClientProvider } from "@tanstack/solid-query";
import { FileRoutes } from "@solidjs/start/router";
import { Suspense } from "solid-js";
import { ChatProvider } from "~/context/ChatContext";
import "./app.css";

export default function App() {
  const queryClient = new QueryClient();

  return (
    <Router
      root={props => (
        <QueryClientProvider client={queryClient}>
          <ChatProvider messages={[]}>
            <Suspense>{props.children}</Suspense>
          </ChatProvider>
        </QueryClientProvider>
      )}
    >
      <FileRoutes />
    </Router>
  );
}
