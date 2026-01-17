import { createSignal } from "solid-js";

export type InputHandle = {
  value?: string;
  cursorPosition?: number;
  focus?: () => void;
};

export const useChatInput = () => {
  const [inputValue, setInputValue] = createSignal("");
  const [inputKey, setInputKey] = createSignal(0);
  const [isSending, setIsSending] = createSignal(false);

  return {
    inputValue,
    setInputValue,
    inputKey,
    setInputKey,
    isSending,
    setIsSending,
  };
};

export const handleCtrlW = (inputRef: InputHandle | null) => {
  if (!inputRef) {
    return false;
  }

  const value = inputRef.value ?? "";
  const cursor = inputRef.cursorPosition ?? value.length;
  const beforeCursor = value.slice(0, cursor);
  const afterCursor = value.slice(cursor);
  const trimmed = beforeCursor.replace(/\s+$/, "");
  const newBefore = trimmed.replace(/\S+$/, "");
  const newValue = newBefore + afterCursor;
  const newCursor = newBefore.length;

  if (newValue !== value) {
    inputRef.value = newValue;
    inputRef.cursorPosition = newCursor;
    return true;
  }
  return false;
};
