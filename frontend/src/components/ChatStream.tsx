import { useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { useChatStream } from "@/hooks/useChatStream";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ChatStreamProps {
  messages: ReturnType<typeof useChatStream>["messages"];
}

export function ChatStream({ messages }: ChatStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="flex flex-col max-w-4xl mx-auto w-full pb-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground mt-20">
            <h2 className="text-xl font-semibold mb-2 text-foreground">ORD Experimental Intelligence</h2>
            <p>Ask a question to search reactions, procedures, molecules, or analyze trends.</p>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
