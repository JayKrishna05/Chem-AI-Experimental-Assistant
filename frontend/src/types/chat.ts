export type ChatRole = "user" | "assistant";

export type AssistantStatus = "thinking" | "tool_selected" | "formatting" | "tool_result" | "done" | "error" | "no_tool" | "idle";

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
}

export interface ChatEvent {
  type: AssistantStatus;
  tool?: string;
  filters?: Record<string, unknown>;
  result?: unknown;
  text?: string;
  message?: string;
  question?: string;
}
