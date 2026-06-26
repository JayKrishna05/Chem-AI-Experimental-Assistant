import { API_BASE_URL, APIError } from "./api";
import { ChatEvent } from "@/types/chat";

export interface SendMessageOptions {
  plannerProvider?: string;
  plannerModel?: string;
  plannerTimeout?: number;
  formatterProvider?: string;
  formatterModel?: string;
  formatterTimeout?: number;
  toolResultOverride?: Record<string, any>;
  toolNameOverride?: string;
}

export async function streamChat(
  content: string,
  options: SendMessageOptions,
  onEvent: (event: ChatEvent) => void
): Promise<void> {
  const url = `${API_BASE_URL}/chat`;
  
  const body: Record<string, unknown> = { message: content };
  if (options.plannerProvider) body.planner_provider = options.plannerProvider;
  if (options.plannerModel)    body.model = options.plannerModel;
  if (options.plannerTimeout)  body.planner_timeout = options.plannerTimeout;
  if (options.formatterProvider) body.formatter_provider = options.formatterProvider;
  if (options.formatterModel)    body.formatter_model = options.formatterModel;
  if (options.formatterTimeout)  body.formatter_timeout = options.formatterTimeout;
  if (options.toolResultOverride) body.tool_result_override = options.toolResultOverride;
  if (options.toolNameOverride) body.tool_name_override = options.toolNameOverride;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let message = "Network error";
    try {
      const errData = await res.json();
      message = errData.detail || errData.message || JSON.stringify(errData);
    } catch (e) {
      message = await res.text();
    }
    throw new APIError(res.status, message);
  }

  if (!res.body) {
    throw new Error("No response body");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let done = false;

  while (!done) {
    const { value, done: readerDone } = await reader.read();
    done = readerDone;

    if (value) {
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.replace("data: ", "").trim();
          if (!dataStr) continue;

          try {
            const event = JSON.parse(dataStr) as ChatEvent;
            onEvent(event);
          } catch (err) {
            console.error("Failed to parse SSE JSON:", dataStr, err);
          }
        }
      }
    }
  }
}
