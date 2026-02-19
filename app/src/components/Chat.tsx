import { type JSX } from "solid-js";

export default function Chat(props: { children: JSX.Element }) {
  return (
    <div class="h-full min-h-0 w-5/6 flex flex-col border-2 border-cyan-600">
      {props.children}
    </div>
  );
}
