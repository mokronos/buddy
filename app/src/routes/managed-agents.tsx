import { useQuery } from "@tanstack/solid-query";
import { createSignal, onMount } from "solid-js";
import { listExternalAgents } from "~/a2a/externalAgents";
import { listManagedAgents } from "~/a2a/managedAgents";
import ManagedAgentCreateSection from "~/components/managed-agents/ManagedAgentCreateSection";
import ManagedAgentsSection from "~/components/managed-agents/ManagedAgentsSection";
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

  onMount(() => setIsClientReady(true));

  const shouldShowLoading = (): boolean =>
    !isClientReady() || managedAgentsQuery.isPending || externalAgentsQuery.isPending;
  const managedAgents = () => (isClientReady() ? managedAgentsQuery.data ?? [] : []);
  const externalAgents = () => (isClientReady() ? externalAgentsQuery.data ?? [] : []);
  const managedQueryErrorMessage = () =>
    managedAgentsQuery.error instanceof Error ? managedAgentsQuery.error.message : null;
  const externalQueryErrorMessage = () =>
    externalAgentsQuery.error instanceof Error ? externalAgentsQuery.error.message : null;

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
  });
  const externalAdmin = useExternalAgentsAdmin({ syncAgentQueries });

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
            feedback={managedAdmin.managedCreateFeedback()}
            externalAgentId={externalAdmin.externalAgentId()}
            externalAgentUrl={externalAdmin.externalAgentUrl()}
            externalUseLegacyCardPath={externalAdmin.externalUseLegacyCardPath()}
            isExternalSubmitting={externalAdmin.createExternalMutation.isPending}
            externalFeedback={externalAdmin.externalCreateFeedback()}
            onExternalAgentIdChange={externalAdmin.setExternalAgentId}
            onExternalAgentUrlChange={externalAdmin.setExternalAgentUrl}
            onExternalUseLegacyCardPathChange={externalAdmin.setExternalUseLegacyCardPath}
            onExternalSubmit={externalAdmin.addExternalAgent}
          />

          <ManagedAgentsSection
            managedAgents={managedAgents()}
            externalAgents={externalAgents()}
            shouldShowLoading={shouldShowLoading()}
            managedListFeedback={managedAdmin.managedListFeedback()}
            externalListFeedback={externalAdmin.externalListFeedback()}
            listErrorMessage={managedQueryErrorMessage() ?? externalQueryErrorMessage()}
            managedEditFeedback={managedAdmin.managedEditFeedback()}
            externalEditFeedback={externalAdmin.externalEditFeedback()}
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
    </main>
  );
}
