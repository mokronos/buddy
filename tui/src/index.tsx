import { render } from "@opentui/solid";

import { Root } from "./app/Root";

render(() => <Root />, {
  exitOnCtrlC: true,
  onDestroy: () => process.exit(0),
});
