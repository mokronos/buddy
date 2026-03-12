type ScrollToBottomButtonProps = {
  onClick: () => void;
};

export default function ScrollToBottomButton(props: ScrollToBottomButtonProps) {
  return (
    <button
      type="button"
      onClick={props.onClick}
      class="btn btn-primary btn-sm absolute bottom-4 right-4 z-10 shadow-lg"
    >
      Jump to latest
    </button>
  );
}
