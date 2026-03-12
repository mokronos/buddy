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
import type { ManagedCreateFormState, ToastInput } from "~/components/managed-agents/types";

interface UseManagedAgentsAdminOptions {
  syncAgentQueries: () => Promise<void>;
  waitForManagedAgentRemoval: (managedAgentId: string) => Promise<boolean>;
  notify: (toast: ToastInput) => void;
}

export function useManagedAgentsAdmin(props: UseManagedAgentsAdminOptions) {
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

    const nextForm = createManagedForm();
    const normalizedConfig = normalizeRuntimeConfig(nextForm.config);
    const validationError = validateRuntimeConfig(normalizedConfig);
    if (validationError) {
      props.notify({ kind: "error", message: validationError });
      return;
    }

    setCreateManagedForm({ config: normalizedConfig });

    try {
      const createdAgent = await createManagedMutation.mutateAsync({
        config: normalizedConfig,
      });
      props.notify({
        kind: "success",
        message: `Created agent '${createdAgent.agent_id}'`,
      });
      setCreateManagedForm(createDefaultManagedForm());
      await props.syncAgentQueries();
    } catch (error) {
      props.notify({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to create agent",
      });
    }
  };

  const startAgent = async (managedAgentId: string): Promise<void> => {
    try {
      await startManagedMutation.mutateAsync(managedAgentId);
      props.notify({
        kind: "success",
        message: `Started agent '${managedAgentId}'`,
      });
      await props.syncAgentQueries();
    } catch (error) {
      props.notify({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to start agent",
      });
    }
  };

  const stopAgent = async (managedAgentId: string): Promise<void> => {
    try {
      await stopManagedMutation.mutateAsync(managedAgentId);
      props.notify({
        kind: "success",
        message: `Stopped agent '${managedAgentId}'`,
      });
      await props.syncAgentQueries();
    } catch (error) {
      props.notify({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to stop agent",
      });
    }
  };

  const removeAgent = async (managedAgentId: string): Promise<void> => {
    if (isDeletingManagedAgent(managedAgentId)) {
      return;
    }

    addDeletingManagedAgent(managedAgentId);
    try {
      await deleteManagedMutation.mutateAsync(managedAgentId);
      const removed = await props.waitForManagedAgentRemoval(managedAgentId);
      if (!removed) {
        throw new Error(`Timed out waiting for '${managedAgentId}' to be removed`);
      }

      await props.syncAgentQueries();
      props.notify({
        kind: "success",
        message: `Deleted agent '${managedAgentId}'`,
      });
    } catch (error) {
      props.notify({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to delete agent",
      });
    } finally {
      removeDeletingManagedAgent(managedAgentId);
    }
  };

  const beginEditManagedAgent = async (managedAgentId: string): Promise<void> => {
    try {
      const loadedConfig = await getManagedAgentConfig(managedAgentId);
      setEditingManagedAgentId(managedAgentId);
      setEditingManagedConfig(normalizeRuntimeConfig(loadedConfig));
      setRestartManagedAfterConfigSave(true);
    } catch (error) {
      props.notify({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to load managed agent config",
      });
    }
  };

  const cancelEditManagedAgent = (): void => {
    setEditingManagedAgentId(null);
    setEditingManagedConfig(null);
    setRestartManagedAfterConfigSave(true);
  };

  const saveManagedAgentConfig = async (managedAgentId: string): Promise<void> => {
    const nextConfig = editingManagedConfig();
    if (!nextConfig) {
      props.notify({ kind: "error", message: "No config loaded for editing" });
      return;
    }

    const normalizedConfig = normalizeRuntimeConfig(nextConfig);
    const validationError = validateRuntimeConfig(normalizedConfig);
    if (validationError) {
      props.notify({ kind: "error", message: validationError });
      return;
    }

    setEditingManagedConfig(normalizedConfig);

    try {
      await updateManagedConfigMutation.mutateAsync({
        agentId: managedAgentId,
        config: normalizedConfig,
        restart: restartManagedAfterConfigSave(),
      });
      props.notify({
        kind: "success",
        message: `Updated config for managed agent '${managedAgentId}'`,
      });
      cancelEditManagedAgent();
      await props.syncAgentQueries();
    } catch (error) {
      props.notify({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to update managed agent config",
      });
    }
  };

  return {
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
