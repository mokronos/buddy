import { Router } from "@solidjs/router";
import { FileRoutes } from "@solidjs/start/router";
import { Suspense } from "solid-js";
import { ChatProvider } from "~/context/ChatContext";
import "./app.css";

export default function App() {
  return (
    <Router
      root={props => (
        <ChatProvider messages={[]}>
          <Suspense>{props.children}</Suspense>
        </ChatProvider>
      )}
    >
      <FileRoutes />
    </Router>
  );
}
