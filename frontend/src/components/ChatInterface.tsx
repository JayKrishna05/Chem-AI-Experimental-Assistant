"use client";

import { useChatStream } from "@/hooks/useChatStream";
import { useModels } from "@/hooks/useModels";
import { ChatStream } from "./ChatStream";
import { ChatInput } from "./ChatInput";

import { useState, useEffect } from "react";

export function ChatInterface() {
  const { messages, sendMessage, isGenerating } = useChatStream();
  const { models, currentPlannerModel, currentFormatterModel, formatterTimeout, updateModels } = useModels();
  
  const [timeoutInput, setTimeoutInput] = useState<string>("59");
  const [timeoutError, setTimeoutError] = useState<string | null>(null);

  useEffect(() => {
    setTimeoutInput(formatterTimeout.toString());
  }, [formatterTimeout]);

  const handleApplyTimeout = () => {
    const val = parseFloat(timeoutInput);
    if (isNaN(val) || val < 5 || val > 300) {
      setTimeoutError("5-300s");
      return;
    }
    setTimeoutError(null);
    updateModels(undefined, undefined, val);
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card px-6 py-4 flex flex-col sm:flex-row items-center justify-between shadow-sm z-10 gap-4">
        <h1 className="text-xl font-bold tracking-tight">ORD Assistant</h1>
        
        <div className="flex flex-wrap items-center gap-4 justify-center sm:justify-end">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground font-semibold">Planner:</label>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none max-w-[120px] sm:max-w-none"
              value={currentPlannerModel}
              onChange={(e) => updateModels(e.target.value, undefined)}
            >
              <option value="loading..." disabled>loading...</option>
              {models.map(m => <option key={m} value={m} title={m}>{m.length > 20 ? m.substring(0, 17) + '...' : m}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground font-semibold">Formatter:</label>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none max-w-[120px] sm:max-w-none"
              value={currentFormatterModel}
              onChange={(e) => updateModels(undefined, e.target.value)}
            >
              <option value="loading..." disabled>loading...</option>
              {models.map(m => <option key={m} value={m} title={m}>{m.length > 20 ? m.substring(0, 17) + '...' : m}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground font-semibold">Timeout (s):</label>
            <input 
              type="number"
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none w-16"
              value={timeoutInput}
              onChange={(e) => {
                setTimeoutInput(e.target.value);
                setTimeoutError(null);
              }}
              min="5"
              max="300"
            />
            <button 
              onClick={handleApplyTimeout}
              className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded hover:bg-primary/90"
            >
              Apply
            </button>
            {timeoutError && <span className="text-xs text-destructive">{timeoutError}</span>}
          </div>
          <div className="text-xs text-muted-foreground font-mono ml-2 hidden md:block">Experimental Engine V1</div>
        </div>
      </header>
      
      <main className="flex-1 overflow-hidden flex flex-col relative">
        <ChatStream messages={messages} onSuggestion={(q) => { if (!isGenerating) sendMessage(q); }} />
        <ChatInput onSendMessage={sendMessage} disabled={isGenerating} />
      </main>
    </div>
  );
}
