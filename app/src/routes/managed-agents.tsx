import { useMutation, useQuery } from "@tanstack/solid-query";
import { createSignal, onMount } from "solid-js";
import {
  createExternalAgent,
  deleteExternalAgent,
  listExternalAgents,
  updateExternalAgent,
  type ExternalAgent,
} from "~/a2a/externalAgents";
import {
  createManagedAgent,
  deleteManagedAgent,
  getManagedAgentConfig,
  listManagedAgents,
  startManagedAgent,
  stopManagedAgent,
  updateManagedAgentConfig,
} from "~/a2a/managedAgents";
import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";
import ExternalAgentsSection from "~/components/managed-agents/ExternalAgentsSection";
import ManagedAgentCreateSection from "~/components/managed-agents/ManagedAgentCreateSection";
import ManagedAgentsSection from "~/components/managed-agents/ManagedAgentsSection";
import {
  createDefaultManagedForm,
  normalizeRuntimeConfig,
  validateRuntimeConfig,
} from "~/components/managed-agents/runtimeConfig";
import type { FeedbackState, ManagedCreateFormState } from "~/components/managed-agents/types";
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

  const [managedCreateFeedback, setManagedCreateFeedback] = createSignal<FeedbackState>(null);
  const [managedListFeedback, setManagedListFeedback] = createSignal<FeedbackState>(null);
  const [managedEditFeedback, setManagedEditFeedback] = createSignal<FeedbackState>(null);
  const [externalCreateFeedback, setExternalCreateFeedback] = createSignal<FeedbackState>(null);
  const [externalListFeedback, setExternalListFeedback] = createSignal<FeedbackState>(null);
  const [externalEditFeedback, setExternalEditFeedback] = createSignal<FeedbackState>(null);

  const [createManagedForm, setCreateManagedForm] = createSignal<ManagedCreateFormState>(createDefaultManagedForm());
  const [editingManagedAgentId, setEditingManagedAgentId] = createSignal<string | null>(null);
  const [editingManagedConfig, setEditingManagedConfig] = createSignal<RuntimeAgentConfigPayload | null>(null);
  const [restartManagedAfterConfigSave, setRestartManagedAfterConfigSave] = createSignal(true);

  const [externalAgentId, setExternalAgentId] = createSignal("");
  const [externalAgentUrl, setExternalAgentUrl] = createSignal("");
  const [externalUseLegacyCardPath, setExternalUseLegacyCardPath] = createSignal(false);
  const [editingExternalAgentId, setEditingExternalAgentId] = createSignal<string | null>(null);
  const [editingExternalAgentUrl, setEditingExternalAgentUrl] = createSignal("");
  const [editingExternalUseLegacyCardPath, setEditingExternalUseLegacyCardPath] = createSignal(false);

  const [deletingManagedAgentIds, setDeletingManagedAgentIds] = createSignal<string[]>([]);
  const [isClientReady, setIsClientReady] = createSignal(false);

  onMount(() => setIsClientReady(true));

  const createManagedMutation = useMutation(() => ({ mutationFn: createManagedAgent }));
  const startManagedMutation = useMutation(() => ({ mutationFn: startManagedAgent }));
  const stopManagedMutation = useMutation(() => ({ mutationFn: stopManagedAgent }));
  const deleteManagedMutation = useMutation(() => ({ mutationFn: deleteManagedAgent }));
  const updateManagedConfigMutation = useMutation(() => ({
    mutationFn: (variables: { agentId: string; config: RuntimeAgentConfigPayload; restart: boolean }) =>
      updateManagedAgentConfig(variables.agentId, {
        config: variables.config,
        restart: variables.restart,
      }),
  }));
  const createExternalMutation = useMutation(() => ({ mutationFn: createExternalAgent }));
  const deleteExternalMutation = useMutation(() => ({ mutationFn: deleteExternalAgent }));
  const updateExternalMutation = useMutation(() => ({
    mutationFn: (variables: { agentId: string; base_url: string; use_legacy_card_path: boolean }) =>
      updateExternalAgent(variables.agentId, {
        base_url: variables.base_url,
        use_legacy_card_path: variables.use_legacy_card_path,
      }),
  }));

  const shouldShowLoading = (): boolean =>
    !isClientReady() || managedAgentsQuery.isPending || externalAgentsQuery.isPending;
  const managedAgents = () => (isClientReady() ? managedAgentsQuery.data ?? [] : []);
  const externalAgents = () => (isClientReady() ? externalAgentsQuery.data ?? [] : []);
  const managedQueryErrorMessage = () =>
    managedAgentsQuery.error instanceof Error ? managedAgentsQuery.error.message : null;
  const externalQueryErrorMessage = () =>
    externalAgentsQuery.error instanceof Error ? externalAgentsQuery.error.message : null;

  const isDeletingManagedAgent = (managedAgentId: string): boolean =>
    deletingManagedAgentIds().some((id) => id === managedAgentId);

  const addDeletingManagedAgent = (managedAgentId: string): void => {
    setDeletingManagedAgentIds((current) =>
      current.some((id) => id === managedAgentId) ? current : [...current, managedAgentId],
    );
  };

  const removeDeletingManagedAgent = (managedAgentId: string): void => {
    setDeletingManagedAgentIds((current) => current.filter((id) => id !== managedAgentId));
  };

  const syncAgentQueries = async (): Promise<void> => {
    await Promise.all([managedAgentsQuery.refetch(), externalAgentsQuery.refetch()]);
    await refreshAgents();
  };

  const clearManagedFeedback = (): void => {
    setManagedCreateFeedback(null);
    setManagedListFeedback(null);
    setManagedEditFeedback(null);
  };

  const clearExternalFeedback = (): void => {
    setExternalCreateFeedback(null);
    setExternalListFeedback(null);
    setExternalEditFeedback(null);
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

  const createAgent = async (event: SubmitEvent): Promise<void> => {
    event.preventDefault();
    clearManagedFeedback();

    const nextForm = createManagedForm();
    const normalizedConfig = normalizeRuntimeConfig(nextForm.config);
    const validationError = validateRuntimeConfig(normalizedConfig);
    if (validationError) {
      setManagedCreateFeedback({ kind: "error", message: validationError });
      return;
    }

    const trimmedImage = nextForm.image.trim();
    const trimmedConfigMountPath = nextForm.config_mount_path.trim();
    if (trimmedImage.length === 0) {
      setManagedCreateFeedback({ kind: "error", message: "Container image is required" });
      return;
    }
    if (trimmedConfigMountPath.length === 0) {
      setManagedCreateFeedback({ kind: "error", message: "Config mount path is required" });
      return;
    }

    setCreateManagedForm({
      image: trimmedImage,
      config_mount_path: trimmedConfigMountPath,
      config: normalizedConfig,
    });

    try {
      await createManagedMutation.mutateAsync({
        agent_id: normalizedConfig.agent.id,
        image: trimmedImage,
        config_mount_path: trimmedConfigMountPath,
        config: normalizedConfig,
      });
      setManagedCreateFeedback({
        kind: "success",
        message: `Created agent '${normalizedConfig.agent.id}'`,
      });
      setCreateManagedForm(createDefaultManagedForm());
      await syncAgentQueries();
    } catch (error) {
      setManagedCreateFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to create agent",
      });
    }
  };

  const startAgent = async (managedAgentId: string): Promise<void> => {
    clearManagedFeedback();
    try {
      await startManagedMutation.mutateAsync(managedAgentId);
      setManagedListFeedback({
        kind: "success",
        message: `Started agent '${managedAgentId}'`,
      });
      await syncAgentQueries();
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to start agent",
      });
    }
  };

  const stopAgent = async (managedAgentId: string): Promise<void> => {
    clearManagedFeedback();
    try {
      await stopManagedMutation.mutateAsync(managedAgentId);
      setManagedListFeedback({
        kind: "success",
        message: `Stopped agent '${managedAgentId}'`,
      });
      await syncAgentQueries();
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to stop agent",
      });
    }
  };

  const removeAgent = async (managedAgentId: string): Promise<void> => {
    if (isDeletingManagedAgent(managedAgentId)) {
      return;
    }

    clearManagedFeedback();
    addDeletingManagedAgent(managedAgentId);
    try {
      await deleteManagedMutation.mutateAsync(managedAgentId);
      const removed = await waitForManagedAgentRemoval(managedAgentId);
      if (!removed) {
        throw new Error(`Timed out waiting for '${managedAgentId}' to be removed`);
      }

      await syncAgentQueries();
      setManagedListFeedback({
        kind: "success",
        message: `Deleted agent '${managedAgentId}'`,
      });
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to delete agent",
      });
    } finally {
      removeDeletingManagedAgent(managedAgentId);
    }
  };

  const beginEditManagedAgent = async (managedAgentId: string): Promise<void> => {
    clearManagedFeedback();
    try {
      const loadedConfig = await getManagedAgentConfig(managedAgentId);
      setEditingManagedAgentId(managedAgentId);
      setEditingManagedConfig(normalizeRuntimeConfig(loadedConfig));
      setRestartManagedAfterConfigSave(true);
    } catch (error) {
      setManagedListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to load managed agent config",
      });
    }
  };

  const cancelEditManagedAgent = (): void => {
    setEditingManagedAgentId(null);
    setEditingManagedConfig(null);
    setRestartManagedAfterConfigSave(true);
    setManagedEditFeedback(null);
  };

  const saveManagedAgentConfig = async (managedAgentId: string): Promise<void> => {
    setManagedListFeedback(null);
    setManagedEditFeedback(null);

    const nextConfig = editingManagedConfig();
    if (!nextConfig) {
      setManagedEditFeedback({ kind: "error", message: "No config loaded for editing" });
      return;
    }

    const normalizedConfig = normalizeRuntimeConfig(nextConfig);
    const validationError = validateRuntimeConfig(normalizedConfig, { lockedAgentId: managedAgentId });
    if (validationError) {
      setManagedEditFeedback({ kind: "error", message: validationError });
      return;
    }

    setEditingManagedConfig(normalizedConfig);

    try {
      await updateManagedConfigMutation.mutateAsync({
        agentId: managedAgentId,
        config: normalizedConfig,
        restart: restartManagedAfterConfigSave(),
      });
      setManagedListFeedback({
        kind: "success",
        message: `Updated config for managed agent '${managedAgentId}'`,
      });
      cancelEditManagedAgent();
      await syncAgentQueries();
    } catch (error) {
      setManagedEditFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to update managed agent config",
      });
    }
  };

  const addExternalAgent = async (event: SubmitEvent): Promise<void> => {
    event.preventDefault();
    clearExternalFeedback();

    const trimmedAgentId = externalAgentId().trim();
    const trimmedAgentUrl = externalAgentUrl().trim();
    if (trimmedAgentId.length === 0) {
      setExternalCreateFeedback({ kind: "error", message: "External agent id is required" });
      return;
    }
    if (trimmedAgentUrl.length === 0) {
      setExternalCreateFeedback({ kind: "error", message: "External agent URL is required" });
      return;
    }

    try {
      await createExternalMutation.mutateAsync({
        agent_id: trimmedAgentId,
        base_url: trimmedAgentUrl,
        use_legacy_card_path: externalUseLegacyCardPath(),
      });
      setExternalCreateFeedback({
        kind: "success",
        message: `Added external agent '${trimmedAgentId}'`,
      });
      setExternalAgentId("");
      setExternalAgentUrl("");
      setExternalUseLegacyCardPath(false);
      await syncAgentQueries();
    } catch (error) {
      setExternalCreateFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to add external agent",
      });
    }
  };

  const removeExternalAgent = async (externalId: string): Promise<void> => {
    clearExternalFeedback();
    try {
      await deleteExternalMutation.mutateAsync(externalId);
      setExternalListFeedback({
        kind: "success",
        message: `Deleted external agent '${externalId}'`,
      });
      await syncAgentQueries();
    } catch (error) {
      setExternalListFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to delete external agent",
      });
    }
  };

  const beginEditExternalAgent = (externalAgent: ExternalAgent): void => {
    clearExternalFeedback();
    setEditingExternalAgentId(externalAgent.agent_id);
    setEditingExternalAgentUrl(externalAgent.base_url);
    setEditingExternalUseLegacyCardPath(externalAgent.use_legacy_card_path);
  };

  const cancelEditExternalAgent = (): void => {
    setEditingExternalAgentId(null);
    setEditingExternalAgentUrl("");
    setEditingExternalUseLegacyCardPath(false);
    setExternalEditFeedback(null);
  };

  const saveExternalAgentEdit = async (agentId: string): Promise<void> => {
    setExternalListFeedback(null);
    setExternalEditFeedback(null);

    const trimmedUrl = editingExternalAgentUrl().trim();
    if (trimmedUrl.length === 0) {
      setExternalEditFeedback({ kind: "error", message: "External agent URL is required" });
      return;
    }

    try {
      await updateExternalMutation.mutateAsync({
        agentId,
        base_url: trimmedUrl,
        use_legacy_card_path: editingExternalUseLegacyCardPath(),
      });
      setExternalListFeedback({
        kind: "success",
        message: `Updated external agent '${agentId}'`,
      });
      cancelEditExternalAgent();
      await syncAgentQueries();
    } catch (error) {
      setExternalEditFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to update external agent",
      });
    }
  };

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
                  Create, run, and edit Docker-backed agent containers with explicit runtime fields. YAML editing is
                  disabled; every supported config value is exposed as a structured form.
                </p>
              </div>
            </div>
          </div>

          <ManagedAgentCreateSection
            form={createManagedForm()}
            onFormChange={setCreateManagedForm}
            onSubmit={createAgent}
            isSubmitting={createManagedMutation.isPending}
            feedback={managedCreateFeedback()}
          />

          <ManagedAgentsSection
            agents={managedAgents()}
            shouldShowLoading={shouldShowLoading()}
            listFeedback={managedListFeedback()}
            listErrorMessage={managedQueryErrorMessage()}
            editFeedback={managedEditFeedback()}
            editingAgentId={editingManagedAgentId()}
            editingConfig={editingManagedConfig()}
            restartAfterSave={restartManagedAfterConfigSave()}
            isSavingEdit={updateManagedConfigMutation.isPending}
            isDeletingAgent={isDeletingManagedAgent}
            onRefresh={() => {
              void syncAgentQueries();
            }}
            onStart={(agentId) => {
              void startAgent(agentId);
            }}
            onStop={(agentId) => {
              void stopAgent(agentId);
            }}
            onBeginEdit={(agentId) => {
              void beginEditManagedAgent(agentId);
            }}
            onDelete={(agentId) => {
              void removeAgent(agentId);
            }}
            onEditingConfigChange={setEditingManagedConfig}
            onRestartAfterSaveChange={setRestartManagedAfterConfigSave}
            onSaveEdit={(agentId) => {
              void saveManagedAgentConfig(agentId);
            }}
            onCancelEdit={cancelEditManagedAgent}
          />

          <ExternalAgentsSection
            agents={externalAgents()}
            shouldShowLoading={shouldShowLoading()}
            createFeedback={externalCreateFeedback()}
            listFeedback={externalListFeedback()}
            listErrorMessage={externalQueryErrorMessage()}
            editFeedback={externalEditFeedback()}
            externalAgentId={externalAgentId()}
            externalAgentUrl={externalAgentUrl()}
            externalUseLegacyCardPath={externalUseLegacyCardPath()}
            editingExternalAgentId={editingExternalAgentId()}
            editingExternalAgentUrl={editingExternalAgentUrl()}
            editingExternalUseLegacyCardPath={editingExternalUseLegacyCardPath()}
            isCreating={createExternalMutation.isPending}
            isUpdating={updateExternalMutation.isPending}
            onExternalAgentIdChange={setExternalAgentId}
            onExternalAgentUrlChange={setExternalAgentUrl}
            onExternalUseLegacyCardPathChange={setExternalUseLegacyCardPath}
            onEditingExternalAgentUrlChange={setEditingExternalAgentUrl}
            onEditingExternalUseLegacyCardPathChange={setEditingExternalUseLegacyCardPath}
            onSubmit={addExternalAgent}
            onBeginEdit={beginEditExternalAgent}
            onCancelEdit={cancelEditExternalAgent}
            onSaveEdit={(agentId) => {
              void saveExternalAgentEdit(agentId);
            }}
            onDelete={(agentId) => {
              void removeExternalAgent(agentId);
            }}
          />
        </div>
      </div>
    </main>
  );
}
