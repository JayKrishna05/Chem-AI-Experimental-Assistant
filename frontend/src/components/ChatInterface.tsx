"use client";

import { useChatStream } from "@/hooks/useChatStream";
import { useModels } from "@/hooks/useModels";
import { ChatStream } from "./ChatStream";
import { ChatInput } from "./ChatInput";

export function ChatInterface() {
  const { messages, sendMessage, isGenerating } = useChatStream();
  const { models, currentPlannerModel, currentFormatterModel, updateModels } = useModels();

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card px-6 py-4 flex flex-col sm:flex-row items-center justify-between shadow-sm z-10 gap-4">
        <h1 className="text-xl font-bold tracking-tight">ORD Assistant</h1>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground font-semibold">Planner:</label>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none"
              value={currentPlannerModel}
              onChange={(e) => updateModels(e.target.value, undefined)}
            >
              <option value="loading..." disabled>loading...</option>
              {models.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground font-semibold">Formatter:</label>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none"
              value={currentFormatterModel}
              onChange={(e) => updateModels(undefined, e.target.value)}
            >
              <option value="loading..." disabled>loading...</option>
              {models.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="text-xs text-muted-foreground font-mono ml-4 hidden md:block">Experimental Engine V1</div>
        </div>
      </header>
      
      <main className="flex-1 overflow-hidden flex flex-col relative">
        <ChatStream messages={messages} />
        <ChatInput onSendMessage={sendMessage} disabled={isGenerating} />
      </main>
    </div>
  );
}
