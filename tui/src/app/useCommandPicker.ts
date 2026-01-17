import type { SelectOption } from "@opentui/core";
import { createMemo, createSignal } from "solid-js";

import type { SlashCommand } from "../utils/commands";
import {
  SLASH_COMMANDS,
  filterSlashCommands,
  shouldShowCommandPicker,
  toCommandInput,
} from "../utils/commands";

export type SlashCommandWithHandler = SlashCommand & {
  run: () => Promise<void> | void;
};

export const useCommandPicker = (inputValue: () => string) => {
  const [showCommandPicker, setShowCommandPicker] = createSignal(false);
  const [selectedCommandIndex, setSelectedCommandIndex] = createSignal(0);

  const filteredCommands = createMemo(() =>
    filterSlashCommands(SLASH_COMMANDS, inputValue()).slice(0, 8),
  );

  const commandOptions = createMemo(() =>
    filteredCommands().map((command) => ({
      name: `/${command.name}`,
      description: command.description,
      value: command.name,
    })),
  );

  const commandPickerKey = createMemo(
    () =>
      `command-picker-${showCommandPicker()}-${inputValue()}-${commandOptions().length}-${selectedCommandIndex()}`,
  );

  const showCommandPickerResolved = createMemo(
    () => showCommandPicker() && commandOptions().length > 0,
  );

  return {
    filteredCommands,
    commandOptions,
    commandPickerKey,
    showCommandPicker,
    setShowCommandPicker,
    selectedCommandIndex,
    setSelectedCommandIndex,
    showCommandPickerResolved,
  };
};

export const handleCommandNavigation = (
  key: { name: string; ctrl?: boolean },
  showCommandPickerResolved: () => boolean,
  commandOptions: () => SelectOption[],
  selectedCommandIndex: () => number,
  setSelectedCommandIndex: (value: number) => void,
  setShowCommandPicker: (value: boolean) => void,
  filteredCommands: () => SlashCommand[],
) => {
  if (!showCommandPickerResolved()) {
    return false;
  }

  if (key.ctrl && key.name === "n") {
    setSelectedCommandIndex((prev) => Math.min(prev + 1, commandOptions().length - 1));
    return true;
  }
  if (key.ctrl && key.name === "p") {
    setSelectedCommandIndex((prev) => Math.max(prev - 1, 0));
    return true;
  }
  if (key.name === "up") {
    setSelectedCommandIndex((prev) => Math.max(prev - 1, 0));
    return true;
  }
  if (key.name === "down") {
    setSelectedCommandIndex((prev) => Math.min(prev + 1, commandOptions().length - 1));
    return true;
  }
  if (key.name === "escape") {
    setShowCommandPicker(false);
    return true;
  }
  if (key.name === "enter") {
    const selected = filteredCommands()[selectedCommandIndex()];
    if (selected) {
      return { action: "insert", command: toCommandInput(selected) };
    }
  }

  return false;
};

export const updateCommandPickerVisibility = (
  inputValue: string,
  setShowCommandPicker: (value: boolean) => void,
  setSelectedCommandIndex: (value: number) => void,
) => {
  const shouldShow = shouldShowCommandPicker(inputValue);
  setShowCommandPicker(shouldShow);
  if (shouldShow) {
    setSelectedCommandIndex(0);
  }
};
