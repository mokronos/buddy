import MarkdownIt from "markdown-it";

interface MarkdownContentProps {
  content: string;
}

const markdown = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
});

export default function MarkdownContent(props: MarkdownContentProps) {
  return (
    <div
      class="text-gray-100 break-words [&_a]:text-blue-300 [&_a]:underline [&_code]:bg-slate-800 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_pre]:bg-slate-800 [&_pre]:p-3 [&_pre]:rounded [&_pre]:overflow-x-auto [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:mb-2 [&_p:last-child]:mb-0"
      innerHTML={markdown.render(props.content)}
    />
  );
}
