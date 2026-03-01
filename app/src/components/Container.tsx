import { type JSX } from "solid-js";

export default function Container(props: { children: JSX.Element }) {
  return (
    <div class="flex min-h-0 flex-1">
      {props.children}
    </div>
  );
}
