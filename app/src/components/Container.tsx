import { type JSX } from "solid-js";

export default function Container(props: { children: JSX.Element }) {
  return (
    <div class="flex h-screen">
      {props.children}
    </div>
  );
}
