import { useState, useEffect, useCallback } from "react";
import { ModelsResponse, ProvidersResponse, CurrentModelsResponse, SetModelsRequest } from "@/types/chat";
import { fetchJson } from "@/services/api";

export function useModels() {
  const [providers, setProviders] = useState<string[]>(["ollama"]);

  // Per-provider model lists
  const [modelsByProvider, setModelsByProvider] = useState<Record<string, string[]>>({
    ollama: [],
    groq: [],
    openai: [],
    anthropic: [],
    gemini: [],
  });

  const [providerStatus, setProviderStatus] = useState<Record<string, { available: boolean; error?: string }>>({});

  const [currentPlannerProvider, setCurrentPlannerProvider] = useState<string>("ollama");
  const [currentPlannerModel, setCurrentPlannerModel] = useState<string>("loading...");
  const [plannerTimeout, setPlannerTimeout] = useState<number>(59.0);

  const [currentFormatterProvider, setCurrentFormatterProvider] = useState<string>("ollama");
  const [currentFormatterModel, setCurrentFormatterModel] = useState<string>("loading...");
  const [formatterTimeout, setFormatterTimeout] = useState<number>(59.0);

  // Fetch models for a specific provider and cache them
  const fetchModelsForProvider = useCallback(async (providerName: string) => {
    try {
      const data = await fetchJson<ModelsResponse>(`/models?provider=${encodeURIComponent(providerName)}`);
      setModelsByProvider((prev) => ({ ...prev, [providerName]: data.models }));
      setProviderStatus((prev) => ({ 
        ...prev, 
        [providerName]: { available: data.available !== false, error: data.error }
      }));
    } catch (err) {
      console.error(`Failed to fetch models for ${providerName}`, err);
    }
  }, []);

  const fetchAll = useCallback(async () => {
    try {
      const [providersData, currentData] = await Promise.all([
        fetchJson<ProvidersResponse>("/providers").catch(() => null),
        fetchJson<CurrentModelsResponse>("/models/current").catch(() => null),
      ]);

      if (providersData) {
        setProviders(providersData.providers);
      }

      if (currentData) {
        setCurrentPlannerProvider(currentData.planner_provider || "ollama");
        setCurrentPlannerModel(currentData.planner_model || "");
        setPlannerTimeout(currentData.planner_timeout ?? 59.0);
        setCurrentFormatterProvider(currentData.formatter_provider || "ollama");
        setCurrentFormatterModel(currentData.formatter_model || "");
        setFormatterTimeout(currentData.formatter_timeout ?? 59.0);

        await Promise.all([
          fetchModelsForProvider(currentData.planner_provider || "ollama"),
          currentData.formatter_provider && currentData.formatter_provider !== currentData.planner_provider
            ? fetchModelsForProvider(currentData.formatter_provider)
            : Promise.resolve(),
        ]);
      }
    } catch (err) {
      console.error("Failed to fetch model state", err);
    }
  }, [fetchModelsForProvider]);

  const updateConfig = useCallback(async (updates: SetModelsRequest) => {
    try {
      const data = await fetchJson<CurrentModelsResponse>("/models/current", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });

      setCurrentPlannerProvider(data.planner_provider || "ollama");
      setCurrentPlannerModel(data.planner_model || "");
      setPlannerTimeout(data.planner_timeout ?? 59.0);
      setCurrentFormatterProvider(data.formatter_provider || "ollama");
      setCurrentFormatterModel(data.formatter_model || "");
      setFormatterTimeout(data.formatter_timeout ?? 59.0);

      if (updates.planner_provider) {
        await fetchModelsForProvider(updates.planner_provider);
      }
      if (updates.formatter_provider) {
        await fetchModelsForProvider(updates.formatter_provider);
      }
    } catch (err) {
      console.error("Failed to update config", err);
    }
  }, [fetchModelsForProvider]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    providers,
    modelsByProvider,
    providerStatus,
    fetchModelsForProvider,

    currentPlannerProvider,
    currentPlannerModel,
    plannerTimeout,

    currentFormatterProvider,
    currentFormatterModel,
    formatterTimeout,

    updateConfig,

    // Convenience derived values for current selections
    plannerModels: modelsByProvider[currentPlannerProvider] || [],
    formatterModels: modelsByProvider[currentFormatterProvider] || [],
  };
}
