"use client";

import { useChatStream } from "@/hooks/useChatStream";
import { ChatStream } from "./ChatStream";
import { ChatInput } from "./ChatInput";

export function ChatInterface() {
  const { messages, sendMessage, isGenerating } = useChatStream();

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card px-6 py-4 flex items-center justify-between shadow-sm z-10">
        <h1 className="text-xl font-bold tracking-tight">ORD Assistant</h1>
        <div className="text-sm text-muted-foreground font-mono">Experimental Engine V1</div>
      </header>
      
      <main className="flex-1 overflow-hidden flex flex-col relative">
        <ChatStream messages={messages} />
        <ChatInput onSendMessage={sendMessage} disabled={isGenerating} />
      </main>
    </div>
  );
}
