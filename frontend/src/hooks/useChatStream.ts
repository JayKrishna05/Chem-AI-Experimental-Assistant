import { useState, useCallback, useRef } from "react";
import { ChatMessage, ChatEvent } from "@/types/chat";
import { streamChat, SendMessageOptions } from "@/services/chat";

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

  const sendMessage = useCallback(async (content: string, toolResultOverride?: Record<string, any>, toolNameOverride?: string) => {
    const userMsgId = crypto.randomUUID();
    const assistantMsgId = crypto.randomUUID();

    const newMessages: ChatMessage[] = [
      { id: userMsgId, role: "user", content },
      { id: assistantMsgId, role: "assistant", content: "", status: "idle" }
    ];

    setMessages((prev) => [...prev, ...newMessages]);
    setIsGenerating(true);

    try {
      const options: SendMessageOptions = {
        ...configRef.current,
        toolResultOverride,
        toolNameOverride
      };
      await streamChat(content, options, (event) => {
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
      });
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

  const addCustomMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  return {
    messages,
    sendMessage,
    addCustomMessage,
    isGenerating,
    updateStreamConfig,
  };
}
