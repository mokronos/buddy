type ScrollToBottomButtonProps = {
  onClick: () => void;
};

export default function ScrollToBottomButton(props: ScrollToBottomButtonProps) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      class="absolute bottom-4 right-4 z-10 rounded-md border border-cyan-500 bg-cyan-900 px-3 py-1 text-sm font-medium text-cyan-100 shadow hover:bg-cyan-800"
    >
      Jump to latest
    </button>
  );
}
