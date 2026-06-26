export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "APIError";
  }
}

export async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const res = await fetch(url, options);
    
    if (!res.ok) {
      let message = "An unknown error occurred";
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
    throw new Error(err instanceof Error ? err.message : "Network error");
  }
}
