import { fetchJson } from "./api";

export interface SystemCapabilities {
  upload_formats: string[];
  max_file_size_mb: number;
  features: string[];
}

export async function getSystemCapabilities(): Promise<SystemCapabilities> {
  return fetchJson<SystemCapabilities>("/system/capabilities");
}

export async function fetchProviders(): Promise<string[]> {
  try {
    const res = await fetchJson<{ models: string[] }>("/models?provider=ollama");
    // Just a basic fallback, actual logic was in useModels
    return ["ollama", "groq"];
  } catch (e) {
    return ["ollama", "groq"];
  }
}

export async function fetchModels(provider: string): Promise<string[]> {
  try {
    const res = await fetchJson<{ models: string[] }>(`/models?provider=${provider}`);
    return res.models;
  } catch (e) {
    return [];
  }
}
