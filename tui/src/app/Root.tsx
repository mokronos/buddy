import { App } from "./App";
import { AppProviders } from "../providers/AppProviders";

export const Root = () => {
  return (
    <AppProviders onStatusMessage={() => {}} onRestore={() => {}}>
      <App />
    </AppProviders>
  );
};
