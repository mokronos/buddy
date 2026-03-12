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
    <header class="border-b border-base-100/10 bg-base-200/80 backdrop-blur">
      <div class="navbar mx-auto max-w-7xl px-4 lg:px-6">
        <div class="flex-1">
          <span class="font-mono text-sm uppercase tracking-[0.3em] text-primary">Buddy</span>
        </div>
        <nav class="flex-none">
          <ul class="menu menu-horizontal gap-2 rounded-box bg-base-100/70 p-1">
            {tabs.map((tab) => {
              const isActive = location.pathname === tab.href;
              return (
                <li>
                  <A href={tab.href} class={isActive ? "active font-semibold" : ""}>
                    {tab.label}
                  </A>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </header>
  );
}
