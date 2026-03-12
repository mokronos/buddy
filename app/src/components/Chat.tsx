import { type JSX } from "solid-js";

export default function Chat(props: { children: JSX.Element }) {
  return (
    <section class="card min-h-[32rem] flex-1 border border-base-100/10 bg-base-100 shadow-2xl">
      {props.children}
    </section>
  );
}
