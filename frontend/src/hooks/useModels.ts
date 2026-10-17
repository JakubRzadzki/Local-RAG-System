import { useCallback, useEffect, useState } from "react";
import { getModels } from "../api/client";
import type { ModelsResponse, OllamaModel } from "../types";
import { useLocalStorage } from "./useLocalStorage";

interface UseModels {
  chatModels: OllamaModel[];
  selected: string;
  select: (name: string) => void;
  embeddingModel: string;
  embeddingInstalled: boolean;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useModels(): UseModels {
  const [data, setData] = useState<ModelsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [stored, setStored] = useLocalStorage<string>("rag.model", "");

  const reload = useCallback(() => {
    setLoading(true);
    getModels()
      .then((response) => {
        setData(response);
        setError(null);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load models"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(reload, [reload]);

  const chatModels = data?.models.filter((m) => m.supports_chat) ?? [];
  // Fall back to the first installed model when the remembered one disappeared.
  const selected = chatModels.some((m) => m.name === stored) ? stored : (chatModels[0]?.name ?? "");

  return {
    chatModels,
    selected,
    select: setStored,
    embeddingModel: data?.embedding_model ?? "",
    embeddingInstalled: data?.embedding_model_installed ?? true,
    loading,
    error,
    reload,
  };
}
