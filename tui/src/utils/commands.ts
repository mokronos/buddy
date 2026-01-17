export type SlashCommand = {
  name: string;
  description: string;
  hint?: string;
  keywords?: string[];
};

export type SlashCommandWithHandler = SlashCommand & {
  run: () => Promise<void> | void;
};

export const SLASH_COMMANDS: SlashCommand[] = [
  {
    name: "connect",
    description: "Reconnect to the server",
    hint: "/connect",
    keywords: ["reconnect", "server"],
  },
  {
    name: "sessions",
    description: "Restore a previous session",
    hint: "/sessions",
    keywords: ["history", "restore"],
  },
];

export const filterSlashCommands = (commands: SlashCommand[], input: string) => {
  const query = input.trim().replace(/^\//, "").toLowerCase();
  if (!query) {
    return commands;
  }
  return commands.filter((command) => {
    const name = command.name.toLowerCase();
    if (name.startsWith(query)) {
      return true;
    }
    if (name.includes(query)) {
      return true;
    }
    return (command.keywords ?? []).some((keyword) => keyword.toLowerCase().includes(query));
  });
};

export const toCommandInput = (command: SlashCommand) => `/${command.name} `;

export const shouldShowCommandPicker = (input: string) => {
  const trimmed = input.trimStart();
  if (!trimmed.startsWith("/")) {
    return false;
  }
  return !trimmed.slice(1).includes(" ");
};
