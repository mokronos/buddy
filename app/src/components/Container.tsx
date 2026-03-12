import { type JSX } from "solid-js";

export default function Container(props: { children: JSX.Element }) {
  return (
    <div class="mx-auto flex min-h-0 w-full max-w-7xl flex-1 flex-col gap-4 px-4 py-4 lg:flex-row lg:px-6">
      {props.children}
    </div>
  );
}
