interface AIMessageProps {
  content: string;
  timestamp?: string;
}

export default function AIMessage(props: AIMessageProps) {
  return (
    <div class="flex justify-start mb-4">
      <div class="bg-slate-700 border border-blue-500 rounded-lg p-3 max-w-[80%]">
        <div class="flex items-center gap-2 mb-1">
          <div class="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
            <span class="text-white text-xs font-bold">AI</span>
          </div>
          <span class="text-xs text-gray-400">Assistant</span>
          {props.timestamp && (
            <span class="text-xs text-gray-500">{props.timestamp}</span>
          )}
        </div>
        <div class="text-gray-100 whitespace-pre-wrap">{props.content}</div>
      </div>
    </div>
  );
}