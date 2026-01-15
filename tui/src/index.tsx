import { createCliRenderer } from "@opentui/core";
import { createRoot } from "@opentui/react";

import { App } from "./app";

const renderer = await createCliRenderer({
  exitOnCtrlC: true,
  onDestroy: () => process.exit(0),
});
createRoot(renderer).render(<App />);
