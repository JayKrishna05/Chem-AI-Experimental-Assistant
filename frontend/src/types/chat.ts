export type ChatRole = "user" | "assistant";

export type AssistantStatus = "thinking" | "tool_selected" | "formatting" | "tool_result" | "done" | "error" | "no_tool" | "idle";

export interface ModelsResponse {
  models: string[];
}

export interface ProvidersResponse {
  providers: string[];
}

export interface CurrentModelsResponse {
  planner_provider: string;
  planner_model: string;
  planner_timeout: number;
  formatter_provider: string;
  formatter_model: string;
  formatter_timeout: number;
}

export interface SetModelsRequest {
  planner_provider?: string;
  planner_model?: string;
  planner_timeout?: number;
  formatter_provider?: string;
  formatter_model?: string;
  formatter_timeout?: number;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string; // Text content (user input or assistant response)
  
  // Assistant specific fields populated during SSE stream
  status?: AssistantStatus;
  toolName?: string;
  filters?: Record<string, unknown>;
  rawData?: unknown;
  errorMessage?: string;
  
  // Execution metadata for Dev Tools
  plannerProvider?: string;
  plannerModel?: string;
  plannerTimeMs?: number;
  toolTimeMs?: number;
  formatterProvider?: string;
  formatterModel?: string;
  formatterTimeMs?: number;
  totalTimeMs?: number;
}

export interface ChatEvent {
  type: AssistantStatus;
  tool?: string;
  filters?: Record<string, unknown>;
  result?: unknown;
  text?: string;
  message?: string;
  question?: string;
  
  // Execution metadata
  plannerProvider?: string;
  plannerModel?: string;
  plannerTimeMs?: number;
  toolTimeMs?: number;
  formatterProvider?: string;
  formatterModel?: string;
  formatterTimeMs?: number;
  totalTimeMs?: number;
}
