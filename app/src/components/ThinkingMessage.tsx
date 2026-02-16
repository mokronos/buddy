interface ThinkingMessageProps {
  content: string;
  timestamp?: string;
}

export default function ThinkingMessage(props: ThinkingMessageProps) {
  return (
    <div class="flex justify-start mb-4">
      <div class="bg-slate-800 border border-cyan-700 rounded-lg p-3 max-w-[80%]">
        <div class="flex items-center gap-2 mb-1">
          <div class="w-6 h-6 bg-cyan-700 rounded-full flex items-center justify-center">
            <span class="text-white text-xs">?</span>
          </div>
          <span class="text-xs text-cyan-300">Thinking</span>
          {props.timestamp && <span class="text-xs text-slate-500">{props.timestamp}</span>}
        </div>
        <div class="text-slate-200 whitespace-pre-wrap text-sm">{props.content}</div>
      </div>
    </div>
  );
}
