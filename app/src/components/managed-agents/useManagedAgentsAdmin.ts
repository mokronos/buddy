import { useMutation } from "@tanstack/solid-query";
import { createSignal } from "solid-js";
import {
  createManagedAgent,
  deleteManagedAgent,
  getManagedAgentConfig,
  startManagedAgent,
  stopManagedAgent,
  updateManagedAgentConfig,
} from "~/a2a/managedAgents";
import type { RuntimeAgentConfigPayload } from "~/a2a/schemas";
import {
  createDefaultManagedForm,
  normalizeRuntimeConfig,
  validateRuntimeConfig,
} from "~/components/managed-agents/runtimeConfig";
import type { FeedbackState, ManagedCreateFormState } from "~/components/managed-agents/types";

interface UseManagedAgentsAdminOptions {
  syncAgentQueries: () => Promise<void>;
  waitForManagedAgentRemoval: (managedAgentId: string) => Promise<boolean>;
}

export function useManagedAgentsAdmin(props: UseManagedAgentsAdminOptions) {
  const [managedCreateFeedback, setManagedCreateFeedback] = createSignal<FeedbackState>(null);
  const [managedListFeedback, setManagedListFeedback] = createSignal<FeedbackState>(null);
  const [managedEditFeedback, setManagedEditFeedback] = createSignal<FeedbackState>(null);
  const [createManagedForm, setCreateManagedForm] = createSignal<ManagedCreateFormState>(createDefaultManagedForm());
  const [editingManagedAgentId, setEditingManagedAgentId] = createSignal<string | null>(null);
  const [editingManagedConfig, setEditingManagedConfig] = createSignal<RuntimeAgentConfigPayload | null>(null);
  const [restartManagedAfterConfigSave, setRestartManagedAfterConfigSave] = createSignal(true);
  const [deletingManagedAgentIds, setDeletingManagedAgentIds] = createSignal<string[]>([]);

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

  const clearManagedFeedback = (): void => {
    setManagedCreateFeedback(null);
    setManagedListFeedback(null);
    setManagedEditFeedback(null);
  };

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
      await props.syncAgentQueries();
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
      await props.syncAgentQueries();
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
      await props.syncAgentQueries();
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
      const removed = await props.waitForManagedAgentRemoval(managedAgentId);
      if (!removed) {
        throw new Error(`Timed out waiting for '${managedAgentId}' to be removed`);
      }

      await props.syncAgentQueries();
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
      await props.syncAgentQueries();
    } catch (error) {
      setManagedEditFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to update managed agent config",
      });
    }
  };

  return {
    managedCreateFeedback,
    managedListFeedback,
    managedEditFeedback,
    createManagedForm,
    setCreateManagedForm,
    editingManagedAgentId,
    editingManagedConfig,
    setEditingManagedConfig,
    restartManagedAfterConfigSave,
    setRestartManagedAfterConfigSave,
    createManagedMutation,
    updateManagedConfigMutation,
    isDeletingManagedAgent,
    createAgent,
    startAgent,
    stopAgent,
    removeAgent,
    beginEditManagedAgent,
    cancelEditManagedAgent,
    saveManagedAgentConfig,
  };
}
