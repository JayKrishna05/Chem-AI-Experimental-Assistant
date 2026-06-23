import { useState, useCallback, useRef } from "react";
import { ChatMessage, ChatEvent } from "@/types/chat";

interface SendMessageOptions {
  plannerProvider?: string;
  plannerModel?: string;
  plannerTimeout?: number;
  formatterProvider?: string;
  formatterModel?: string;
  formatterTimeout?: number;
}

export function useChatStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Config refs — updated by ChatInterface when model/provider dropdowns change.
  // Using refs so sendMessage closure always reads the latest value without
  // needing to be in useCallback's dependency array.
  const configRef = useRef<SendMessageOptions>({});

  const updateStreamConfig = useCallback((opts: SendMessageOptions) => {
    configRef.current = { ...configRef.current, ...opts };
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    const userMsgId = crypto.randomUUID();
    const assistantMsgId = crypto.randomUUID();

    const newMessages: ChatMessage[] = [
      { id: userMsgId, role: "user", content },
      { id: assistantMsgId, role: "assistant", content: "", status: "idle" }
    ];

    setMessages((prev) => [...prev, ...newMessages]);
    setIsGenerating(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      
      // Build the request body — include all config so the backend knows exactly
      // which provider+model to use for each role without relying solely on
      // server-side global state.
      const cfg = configRef.current;
      const body: Record<string, unknown> = { message: content };
      if (cfg.plannerProvider) body.planner_provider = cfg.plannerProvider;
      if (cfg.plannerModel)    body.model = cfg.plannerModel;
      if (cfg.plannerTimeout)  body.planner_timeout = cfg.plannerTimeout;
      if (cfg.formatterProvider) body.formatter_provider = cfg.formatterProvider;
      if (cfg.formatterModel)    body.formatter_model = cfg.formatterModel;
      if (cfg.formatterTimeout)  body.formatter_timeout = cfg.formatterTimeout;

      const res = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
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

                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.id === assistantMsgId) {
                      const updated = { ...msg, status: event.type };

                      if (event.type === "tool_selected") {
                        updated.toolName = event.tool;
                        updated.filters = event.filters;
                      } else if (event.type === "tool_result") {
                        updated.rawData = event.result;
                        updated.content = event.text || "";
                      } else if (event.type === "error" || event.type === "no_tool") {
                        updated.errorMessage = event.message;
                        updated.content = event.message || "";
                      }
                      
                      // Merge timing metadata if present
                      if (event.plannerTimeMs !== undefined) updated.plannerTimeMs = event.plannerTimeMs;
                      if (event.toolTimeMs !== undefined) updated.toolTimeMs = event.toolTimeMs;
                      if (event.formatterTimeMs !== undefined) updated.formatterTimeMs = event.formatterTimeMs;
                      if (event.totalTimeMs !== undefined) updated.totalTimeMs = event.totalTimeMs;
                      if (event.plannerProvider) updated.plannerProvider = event.plannerProvider;
                      if (event.plannerModel) updated.plannerModel = event.plannerModel;
                      if (event.formatterProvider) updated.formatterProvider = event.formatterProvider;
                      if (event.formatterModel) updated.formatterModel = event.formatterModel;
                      
                      return updated;
                    }
                    return msg;
                  })
                );
              } catch (err) {
                console.error("Failed to parse SSE JSON:", dataStr, err);
              }
            }
          }
        }
      }
    } catch (error: unknown) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                status: "error",
                errorMessage: error instanceof Error ? error.message : "Network error",
                content: "An error occurred.",
              }
            : msg
        )
      );
    } finally {
      setIsGenerating(false);
    }
  }, []);

  return {
    messages,
    sendMessage,
    isGenerating,
    updateStreamConfig,
  };
}
