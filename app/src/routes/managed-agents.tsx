import { useQuery } from "@tanstack/solid-query";
import { createEffect, createSignal, onMount } from "solid-js";
import { listExternalAgents } from "~/a2a/externalAgents";
import { listManagedAgents } from "~/a2a/managedAgents";
import ManagedAgentCreateSection from "~/components/managed-agents/ManagedAgentCreateSection";
import ManagedAgentsSection from "~/components/managed-agents/ManagedAgentsSection";
import ToastViewport from "~/components/managed-agents/ToastViewport";
import type { ToastInput, ToastMessage } from "~/components/managed-agents/types";
import { useExternalAgentsAdmin } from "~/components/managed-agents/useExternalAgentsAdmin";
import { useManagedAgentsAdmin } from "~/components/managed-agents/useManagedAgentsAdmin";
import TopTabs from "~/components/TopTabs";
import { useAgents } from "~/context/AgentsContext";

export default function ManagedAgentsPage() {
  const { refreshAgents } = useAgents();
  const managedAgentsQuery = useQuery(() => ({
    queryKey: ["agents", "managed"],
    queryFn: listManagedAgents,
    suspense: false,
    throwOnError: false,
  }));
  const externalAgentsQuery = useQuery(() => ({
    queryKey: ["agents", "external"],
    queryFn: listExternalAgents,
    suspense: false,
    throwOnError: false,
  }));

  const [isClientReady, setIsClientReady] = createSignal(false);
  const [toasts, setToasts] = createSignal<ToastMessage[]>([]);
  const [lastManagedQueryError, setLastManagedQueryError] = createSignal<string | null>(null);
  const [lastExternalQueryError, setLastExternalQueryError] = createSignal<string | null>(null);
  let toastCounter = 0;

  onMount(() => setIsClientReady(true));

  const shouldShowLoading = (): boolean =>
    !isClientReady() || managedAgentsQuery.isPending || externalAgentsQuery.isPending;
  const managedAgents = () => (isClientReady() ? managedAgentsQuery.data ?? [] : []);
  const externalAgents = () => (isClientReady() ? externalAgentsQuery.data ?? [] : []);
  const managedQueryErrorMessage = () =>
    managedAgentsQuery.error instanceof Error ? managedAgentsQuery.error.message : null;
  const externalQueryErrorMessage = () =>
    externalAgentsQuery.error instanceof Error ? externalAgentsQuery.error.message : null;

  const notify = (toast: ToastInput): void => {
    const id = toastCounter;
    toastCounter += 1;
    setToasts((current) => [...current, { id, ...toast }]);
    setTimeout(() => {
      setToasts((current) => current.filter((item) => item.id !== id));
    }, 4000);
  };

  createEffect(() => {
    const message = managedQueryErrorMessage();
    if (!message) {
      setLastManagedQueryError(null);
      return;
    }
    if (message === lastManagedQueryError()) {
      return;
    }
    setLastManagedQueryError(message);
    notify({ kind: "error", message });
  });

  createEffect(() => {
    const message = externalQueryErrorMessage();
    if (!message) {
      setLastExternalQueryError(null);
      return;
    }
    if (message === lastExternalQueryError()) {
      return;
    }
    setLastExternalQueryError(message);
    notify({ kind: "error", message });
  });

  const syncAgentQueries = async (): Promise<void> => {
    await Promise.all([managedAgentsQuery.refetch(), externalAgentsQuery.refetch()]);
    await refreshAgents();
  };

  const waitForManagedAgentRemoval = async (managedAgentId: string): Promise<boolean> => {
    const maxAttempts = 20;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const result = await managedAgentsQuery.refetch();
      const agents = result.data ?? [];
      if (!agents.some((agent) => agent.agent_id === managedAgentId)) {
        return true;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    return false;
  };
  const managedAdmin = useManagedAgentsAdmin({
    syncAgentQueries,
    waitForManagedAgentRemoval,
    notify,
  });
  const externalAdmin = useExternalAgentsAdmin({ syncAgentQueries, notify });

  return (
    <main class="flex h-screen flex-col overflow-hidden">
      <TopTabs />
      <div class="min-h-0 flex-1 overflow-hidden px-4 py-4 lg:px-6">
        <div class="mx-auto grid h-full w-full max-w-7xl gap-6 lg:grid-cols-[minmax(320px,420px)_minmax(0,1fr)]">
          <ManagedAgentCreateSection
            form={managedAdmin.createManagedForm()}
            onFormChange={managedAdmin.setCreateManagedForm}
            onSubmit={managedAdmin.createAgent}
            isSubmitting={managedAdmin.createManagedMutation.isPending}
            externalAgentId={externalAdmin.externalAgentId()}
            externalAgentUrl={externalAdmin.externalAgentUrl()}
            externalUseLegacyCardPath={externalAdmin.externalUseLegacyCardPath()}
            isExternalSubmitting={externalAdmin.createExternalMutation.isPending}
            onExternalAgentIdChange={externalAdmin.setExternalAgentId}
            onExternalAgentUrlChange={externalAdmin.setExternalAgentUrl}
            onExternalUseLegacyCardPathChange={externalAdmin.setExternalUseLegacyCardPath}
            onExternalSubmit={externalAdmin.addExternalAgent}
          />

          <ManagedAgentsSection
            managedAgents={managedAgents()}
            externalAgents={externalAgents()}
            shouldShowLoading={shouldShowLoading()}
            editingManagedAgentId={managedAdmin.editingManagedAgentId()}
            editingExternalAgentId={externalAdmin.editingExternalAgentId()}
            editingManagedConfig={managedAdmin.editingManagedConfig()}
            editingExternalAgentUrl={externalAdmin.editingExternalAgentUrl()}
            editingExternalUseLegacyCardPath={externalAdmin.editingExternalUseLegacyCardPath()}
            restartAfterSave={managedAdmin.restartManagedAfterConfigSave()}
            isSavingManagedEdit={managedAdmin.updateManagedConfigMutation.isPending}
            isSavingExternalEdit={externalAdmin.updateExternalMutation.isPending}
            isDeletingManagedAgent={managedAdmin.isDeletingManagedAgent}
            onRefresh={() => {
              void syncAgentQueries();
            }}
            onStartManaged={(agentId) => {
              void managedAdmin.startAgent(agentId);
            }}
            onStopManaged={(agentId) => {
              void managedAdmin.stopAgent(agentId);
            }}
            onBeginEditManaged={(agentId) => {
              void managedAdmin.beginEditManagedAgent(agentId);
            }}
            onDeleteManaged={(agentId) => {
              void managedAdmin.removeAgent(agentId);
            }}
            onEditingManagedConfigChange={managedAdmin.setEditingManagedConfig}
            onRestartAfterSaveChange={managedAdmin.setRestartManagedAfterConfigSave}
            onSaveManagedEdit={(agentId) => {
              void managedAdmin.saveManagedAgentConfig(agentId);
            }}
            onCancelManagedEdit={managedAdmin.cancelEditManagedAgent}
            onBeginEditExternal={externalAdmin.beginEditExternalAgent}
            onDeleteExternal={(agentId) => {
              void externalAdmin.removeExternalAgent(agentId);
            }}
            onEditingExternalAgentUrlChange={externalAdmin.setEditingExternalAgentUrl}
            onEditingExternalUseLegacyCardPathChange={externalAdmin.setEditingExternalUseLegacyCardPath}
            onSaveExternalEdit={(agentId) => {
              void externalAdmin.saveExternalAgentEdit(agentId);
            }}
            onCancelExternalEdit={externalAdmin.cancelEditExternalAgent}
          />
        </div>
      </div>
      <ToastViewport toasts={toasts()} />
    </main>
  );
}
