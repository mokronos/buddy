interface WorkingIndicatorProps {
  stopping?: boolean;
}

export default function WorkingIndicator(props: WorkingIndicatorProps) {
  return (
    <div class="mb-4 flex justify-start">
      <div class="alert alert-info max-w-[85%] shadow-sm">
        <span class="loading loading-spinner loading-sm" />
        <span class="text-sm">{props.stopping ? "Stopping..." : "Working..."}</span>
        </div>
    </div>
  );
}
