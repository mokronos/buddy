import { useMutation } from "@tanstack/solid-query";
import { createSignal } from "solid-js";
import {
  createExternalAgent,
  deleteExternalAgent,
  updateExternalAgent,
  type ExternalAgent,
} from "~/a2a/externalAgents";
import type { FeedbackState } from "~/components/managed-agents/types";

interface UseExternalAgentsAdminOptions {
  syncAgentQueries: () => Promise<void>;
}

export function useExternalAgentsAdmin(props: UseExternalAgentsAdminOptions) {
  const [externalCreateFeedback, setExternalCreateFeedback] = createSignal<FeedbackState>(null);
  const [externalListFeedback, setExternalListFeedback] = createSignal<FeedbackState>(null);
  const [externalEditFeedback, setExternalEditFeedback] = createSignal<FeedbackState>(null);
  const [externalAgentId, setExternalAgentId] = createSignal("");
  const [externalAgentUrl, setExternalAgentUrl] = createSignal("");
  const [externalUseLegacyCardPath, setExternalUseLegacyCardPath] = createSignal(false);
  const [editingExternalAgentId, setEditingExternalAgentId] = createSignal<string | null>(null);
  const [editingExternalAgentUrl, setEditingExternalAgentUrl] = createSignal("");
  const [editingExternalUseLegacyCardPath, setEditingExternalUseLegacyCardPath] = createSignal(false);

  const createExternalMutation = useMutation(() => ({ mutationFn: createExternalAgent }));
  const deleteExternalMutation = useMutation(() => ({ mutationFn: deleteExternalAgent }));
  const updateExternalMutation = useMutation(() => ({
    mutationFn: (variables: { agentId: string; base_url: string; use_legacy_card_path: boolean }) =>
      updateExternalAgent(variables.agentId, {
        base_url: variables.base_url,
        use_legacy_card_path: variables.use_legacy_card_path,
      }),
  }));

  const clearExternalFeedback = (): void => {
    setExternalCreateFeedback(null);
    setExternalListFeedback(null);
    setExternalEditFeedback(null);
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
      await props.syncAgentQueries();
    } catch (error) {
      setExternalCreateFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to add external agent",
      });
    }
  };

  const removeExternalAgent = async (agentId: string): Promise<void> => {
    clearExternalFeedback();
    try {
      await deleteExternalMutation.mutateAsync(agentId);
      setExternalListFeedback({
        kind: "success",
        message: `Deleted external agent '${agentId}'`,
      });
      await props.syncAgentQueries();
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
      await props.syncAgentQueries();
    } catch (error) {
      setExternalEditFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Failed to update external agent",
      });
    }
  };

  return {
    externalCreateFeedback,
    externalListFeedback,
    externalEditFeedback,
    externalAgentId,
    setExternalAgentId,
    externalAgentUrl,
    setExternalAgentUrl,
    externalUseLegacyCardPath,
    setExternalUseLegacyCardPath,
    editingExternalAgentId,
    editingExternalAgentUrl,
    setEditingExternalAgentUrl,
    editingExternalUseLegacyCardPath,
    setEditingExternalUseLegacyCardPath,
    createExternalMutation,
    updateExternalMutation,
    addExternalAgent,
    removeExternalAgent,
    beginEditExternalAgent,
    cancelEditExternalAgent,
    saveExternalAgentEdit,
  };
}
