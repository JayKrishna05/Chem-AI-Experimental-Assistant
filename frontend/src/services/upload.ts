import { API_BASE_URL, APIError } from "./api";

export interface ComparisonReport {
  experiment_id: string;
  is_valid: boolean;
  warnings: string[];
  confidence_score: number;
  comparisons: {
    similar_reactions?: {
      total_matching: number;
      top_matches: Array<{ reaction_id: string; reaction_type: string }>;
    };
    optimal_conditions?: {
      reaction_type: string;
      best_catalyst: string;
      best_avg_yield: number;
      user_yield: number;
      yield_classification?: string;
    };
    temperature_profile?: {
      user_temperature: number;
      db_average_temperature: number;
      difference: number;
      is_anomalous: boolean;
    };
  };
}

export interface CompareExperimentResponse {
  comparisons: ComparisonReport[];
}

export async function uploadAndCompareExperiment(file: File): Promise<CompareExperimentResponse> {
  const url = `${API_BASE_URL}/experiments/compare`;
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(url, {
      method: "POST",
      body: formData,
      // Note: we don't set Content-Type header here; fetch will set it with the correct boundary for FormData
    });

    if (!res.ok) {
      let message = "Upload failed";
      try {
        const errData = await res.json();
        message = errData.detail || errData.message || JSON.stringify(errData);
      } catch (e) {
        message = await res.text();
      }
      throw new APIError(res.status, message);
    }

    return await res.json();
  } catch (err) {
    if (err instanceof APIError) {
      throw err;
    }
    throw new Error(err instanceof Error ? err.message : "Network error during upload");
  }
}
