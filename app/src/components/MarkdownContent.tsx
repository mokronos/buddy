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
      class="prose prose-sm max-w-none break-words prose-invert [&_a]:link [&_a]:link-primary [&_code]:rounded-md [&_code]:bg-base-300 [&_code]:px-1 [&_code]:py-0.5 [&_pre]:rounded-box [&_pre]:bg-base-300 [&_ul]:pl-5 [&_ol]:pl-5"
      innerHTML={markdown.render(props.content)}
    />
  );
}
