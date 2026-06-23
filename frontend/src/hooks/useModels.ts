import { useState, useEffect, useCallback } from "react";
import { ModelsResponse, ProvidersResponse, CurrentModelsResponse, SetModelsRequest } from "@/types/chat";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

  const [currentPlannerProvider, setCurrentPlannerProvider] = useState<string>("ollama");
  const [currentPlannerModel, setCurrentPlannerModel] = useState<string>("loading...");
  const [plannerTimeout, setPlannerTimeout] = useState<number>(59.0);

  const [currentFormatterProvider, setCurrentFormatterProvider] = useState<string>("ollama");
  const [currentFormatterModel, setCurrentFormatterModel] = useState<string>("loading...");
  const [formatterTimeout, setFormatterTimeout] = useState<number>(59.0);

  // Fetch models for a specific provider and cache them
  const fetchModelsForProvider = useCallback(async (providerName: string) => {
    try {
      const res = await fetch(`${API_URL}/models?provider=${encodeURIComponent(providerName)}`);
      if (res.ok) {
        const data = (await res.json()) as ModelsResponse;
        setModelsByProvider((prev) => ({ ...prev, [providerName]: data.models }));
      }
    } catch (err) {
      console.error(`Failed to fetch models for ${providerName}`, err);
    }
  }, []);

  const fetchAll = useCallback(async () => {
    try {
      const [providersRes, currentRes] = await Promise.all([
        fetch(`${API_URL}/providers`),
        fetch(`${API_URL}/models/current`),
      ]);

      if (providersRes.ok) {
        const data = (await providersRes.json()) as ProvidersResponse;
        setProviders(data.providers);
      }

      if (currentRes.ok) {
        const data = (await currentRes.json()) as CurrentModelsResponse;
        setCurrentPlannerProvider(data.planner_provider || "ollama");
        setCurrentPlannerModel(data.planner_model || "");
        setPlannerTimeout(data.planner_timeout ?? 59.0);
        setCurrentFormatterProvider(data.formatter_provider || "ollama");
        setCurrentFormatterModel(data.formatter_model || "");
        setFormatterTimeout(data.formatter_timeout ?? 59.0);

        // Pre-load model lists for both active providers
        await Promise.all([
          fetchModelsForProvider(data.planner_provider || "ollama"),
          data.formatter_provider && data.formatter_provider !== data.planner_provider
            ? fetchModelsForProvider(data.formatter_provider)
            : Promise.resolve(),
        ]);
      }
    } catch (err) {
      console.error("Failed to fetch model state", err);
    }
  }, [fetchModelsForProvider]);

  const updateConfig = useCallback(async (updates: SetModelsRequest) => {
    try {
      const res = await fetch(`${API_URL}/models/current`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });

      if (res.ok) {
        const data = (await res.json()) as CurrentModelsResponse;
        setCurrentPlannerProvider(data.planner_provider || "ollama");
        setCurrentPlannerModel(data.planner_model || "");
        setPlannerTimeout(data.planner_timeout ?? 59.0);
        setCurrentFormatterProvider(data.formatter_provider || "ollama");
        setCurrentFormatterModel(data.formatter_model || "");
        setFormatterTimeout(data.formatter_timeout ?? 59.0);

        // If a new provider was selected, fetch its model list
        if (updates.planner_provider) {
          await fetchModelsForProvider(updates.planner_provider);
        }
        if (updates.formatter_provider) {
          await fetchModelsForProvider(updates.formatter_provider);
        }
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
