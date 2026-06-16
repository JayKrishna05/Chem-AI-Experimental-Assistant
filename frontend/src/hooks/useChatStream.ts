import { useState, useCallback } from "react";
import { ChatMessage, ChatEvent } from "@/types/chat";

export function useChatStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

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
      const res = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content }),
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
            ? { ...msg, status: "error", errorMessage: error instanceof Error ? error.message : "Network error", content: "An error occurred." } 
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
  };
}
