export type ChatRole = "user" | "assistant" | "system";


export type AssistantStatus = "thinking" | "tool_selected" | "formatting" | "tool_result" | "done" | "error" | "no_tool" | "idle";

export interface ModelsResponse {
  models: string[];
  available?: boolean;
  error?: string;
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

export interface ChatRequest {
  message: string;
  planner_provider?: string;
  model?: string;
  planner_timeout?: number;
  formatter_provider?: string;
  formatter_model?: string;
  formatter_timeout?: number;
  tool_result_override?: Record<string, any>;
  tool_name_override?: string;
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
  uploadResult?: any; // CompareExperimentResponse from the upload service
  
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
