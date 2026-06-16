import { useState, useEffect, useCallback } from "react";
import { ModelsResponse, CurrentModelsResponse } from "@/types/chat";

export function useModels() {
  const [models, setModels] = useState<string[]>([]);
  const [currentPlannerModel, setCurrentPlannerModel] = useState<string>("loading...");
  const [currentFormatterModel, setCurrentFormatterModel] = useState<string>("loading...");

  const fetchModels = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const [listRes, currentRes] = await Promise.all([
        fetch(`${apiUrl}/models`),
        fetch(`${apiUrl}/models/current`)
      ]);

      if (listRes.ok) {
        const listData = (await listRes.json()) as ModelsResponse;
        setModels(listData.models);
      }

      if (currentRes.ok) {
        const currentData = (await currentRes.json()) as CurrentModelsResponse;
        setCurrentPlannerModel(currentData.planner_model);
        setCurrentFormatterModel(currentData.formatter_model);
      }
    } catch (err) {
      console.error("Failed to fetch models", err);
    }
  }, []);

  const updateModels = async (plannerModel?: string, formatterModel?: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const body: Record<string, string> = {};
      if (plannerModel) body.planner_model = plannerModel;
      if (formatterModel) body.formatter_model = formatterModel;

      const res = await fetch(`${apiUrl}/models/current`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });

      if (res.ok) {
        const data = (await res.json()) as CurrentModelsResponse;
        setCurrentPlannerModel(data.planner_model);
        setCurrentFormatterModel(data.formatter_model);
      }
    } catch (err) {
      console.error("Failed to update models", err);
    }
  };

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return {
    models,
    currentPlannerModel,
    currentFormatterModel,
    updateModels
  };
}
