import { A, useLocation } from "@solidjs/router";

interface TabItem {
  href: string;
  label: string;
}

const tabs: TabItem[] = [
  { href: "/", label: "Chat" },
  { href: "/managed-agents", label: "Manage Agents" },
  { href: "/agent-logs", label: "Agent Logs" },
];

export default function TopTabs() {
  const location = useLocation();

  return (
    <header class="border-b border-zinc-800 bg-zinc-950 px-4 py-3 text-zinc-100">
      <nav class="mx-auto flex w-full max-w-7xl items-center gap-2">
        {tabs.map((tab) => {
          const isActive = location.pathname === tab.href;
          return (
            <A
              href={tab.href}
              class={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-zinc-100 text-zinc-900"
                  : "border border-zinc-700 text-zinc-300 hover:border-zinc-500 hover:text-zinc-100"
              }`}
            >
              {tab.label}
            </A>
          );
        })}
      </nav>
    </header>
  );
}
