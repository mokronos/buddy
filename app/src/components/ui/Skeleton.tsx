import { splitProps, type JSX } from "solid-js";

type SkeletonProps = JSX.HTMLAttributes<HTMLDivElement>;

export default function Skeleton(props: SkeletonProps) {
  const [local, rest] = splitProps(props, ["class"]);

  return (
    <div
      aria-hidden="true"
      class={`animate-pulse rounded-md bg-zinc-800/80 ${local.class ?? ""}`}
      {...rest}
    />
  );
}
