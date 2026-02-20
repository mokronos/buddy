import MarkdownContent from "./MarkdownContent";

interface HumanMessageProps {
  content: string;
  timestamp?: string;
}

export default function HumanMessage(props: HumanMessageProps) {
  return (
    <div class="flex justify-end mb-4">
      <div class="bg-slate-600 border border-green-500 rounded-lg p-3 max-w-[80%]">
        <div class="flex items-center gap-2 mb-1 justify-end">
          {props.timestamp && (
            <span class="text-xs text-gray-500">{props.timestamp}</span>
          )}
          <span class="text-xs text-gray-400">You</span>
          <div class="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
            <span class="text-white text-xs font-bold">H</span>
          </div>
        </div>
        <MarkdownContent content={props.content} />
      </div>
    </div>
  );
}
