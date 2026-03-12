import { useQuery } from "@tanstack/solid-query";
import { createSignal, onMount } from "solid-js";
import { listExternalAgents } from "~/a2a/externalAgents";
import { listManagedAgents } from "~/a2a/managedAgents";
import ExternalAgentsSection from "~/components/managed-agents/ExternalAgentsSection";
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
    <main class="flex min-h-screen flex-col">
      <TopTabs />
      <div class="min-h-0 flex-1 overflow-y-auto px-4 py-4 lg:px-6">
        <div class="mx-auto flex w-full max-w-6xl flex-col gap-6">
          <div class="hero overflow-hidden rounded-box border border-base-100/10 bg-base-100 shadow-xl">
            <div class="hero-content w-full justify-start bg-[linear-gradient(135deg,rgba(255,255,255,0.05),transparent)] p-6">
              <div>
                <div class="badge badge-primary badge-outline mb-3">Control Plane</div>
                <h1 class="text-3xl font-semibold">Managed Agents</h1>
                <p class="mt-2 max-w-3xl text-sm text-base-content/70">
                  Create, run, and edit Docker-backed agent containers. Runtime infrastructure values are auto-managed,
                  while model behavior and MCP servers are configured through the structured form.
                </p>
              </div>
            </div>
          </div>

          <ManagedAgentCreateSection
            form={managedAdmin.createManagedForm()}
            onFormChange={managedAdmin.setCreateManagedForm}
            onSubmit={managedAdmin.createAgent}
            isSubmitting={managedAdmin.createManagedMutation.isPending}
            feedback={managedAdmin.managedCreateFeedback()}
          />

          <ManagedAgentsSection
            agents={managedAgents()}
            shouldShowLoading={shouldShowLoading()}
            listFeedback={managedAdmin.managedListFeedback()}
            listErrorMessage={managedQueryErrorMessage()}
            editFeedback={managedAdmin.managedEditFeedback()}
            editingAgentId={managedAdmin.editingManagedAgentId()}
            editingConfig={managedAdmin.editingManagedConfig()}
            restartAfterSave={managedAdmin.restartManagedAfterConfigSave()}
            isSavingEdit={managedAdmin.updateManagedConfigMutation.isPending}
            isDeletingAgent={managedAdmin.isDeletingManagedAgent}
            onRefresh={() => {
              void syncAgentQueries();
            }}
            onStart={(agentId) => {
              void managedAdmin.startAgent(agentId);
            }}
            onStop={(agentId) => {
              void managedAdmin.stopAgent(agentId);
            }}
            onBeginEdit={(agentId) => {
              void managedAdmin.beginEditManagedAgent(agentId);
            }}
            onDelete={(agentId) => {
              void managedAdmin.removeAgent(agentId);
            }}
            onEditingConfigChange={managedAdmin.setEditingManagedConfig}
            onRestartAfterSaveChange={managedAdmin.setRestartManagedAfterConfigSave}
            onSaveEdit={(agentId) => {
              void managedAdmin.saveManagedAgentConfig(agentId);
            }}
            onCancelEdit={managedAdmin.cancelEditManagedAgent}
          />

          <ExternalAgentsSection
            agents={externalAgents()}
            shouldShowLoading={shouldShowLoading()}
            createFeedback={externalAdmin.externalCreateFeedback()}
            listFeedback={externalAdmin.externalListFeedback()}
            listErrorMessage={externalQueryErrorMessage()}
            editFeedback={externalAdmin.externalEditFeedback()}
            externalAgentId={externalAdmin.externalAgentId()}
            externalAgentUrl={externalAdmin.externalAgentUrl()}
            externalUseLegacyCardPath={externalAdmin.externalUseLegacyCardPath()}
            editingExternalAgentId={externalAdmin.editingExternalAgentId()}
            editingExternalAgentUrl={externalAdmin.editingExternalAgentUrl()}
            editingExternalUseLegacyCardPath={externalAdmin.editingExternalUseLegacyCardPath()}
            isCreating={externalAdmin.createExternalMutation.isPending}
            isUpdating={externalAdmin.updateExternalMutation.isPending}
            onExternalAgentIdChange={externalAdmin.setExternalAgentId}
            onExternalAgentUrlChange={externalAdmin.setExternalAgentUrl}
            onExternalUseLegacyCardPathChange={externalAdmin.setExternalUseLegacyCardPath}
            onEditingExternalAgentUrlChange={externalAdmin.setEditingExternalAgentUrl}
            onEditingExternalUseLegacyCardPathChange={externalAdmin.setEditingExternalUseLegacyCardPath}
            onSubmit={externalAdmin.addExternalAgent}
            onBeginEdit={externalAdmin.beginEditExternalAgent}
            onCancelEdit={externalAdmin.cancelEditExternalAgent}
            onSaveEdit={(agentId) => {
              void externalAdmin.saveExternalAgentEdit(agentId);
            }}
            onDelete={(agentId) => {
              void externalAdmin.removeExternalAgent(agentId);
            }}
          />
        </div>
      </div>
    </main>
  );
}
