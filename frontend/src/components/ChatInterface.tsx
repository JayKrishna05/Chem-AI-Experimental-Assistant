"use client";

import { useChatStream } from "@/hooks/useChatStream";
import { useModels } from "@/hooks/useModels";
import { useUpload } from "@/hooks/useUpload";
import { ChatStream } from "./ChatStream";
import { ChatInput } from "./ChatInput";
import { UploadPreview } from "./UploadPreview";

import { useState, useEffect } from "react";

export function ChatInterface() {
  const { messages, sendMessage, addCustomMessage, isGenerating, updateStreamConfig } = useChatStream();
  const { uploadExperiment, cancelUpload, uploadProgress, uploadedFile, uploadState, uploadError } = useUpload();
  const { 
    providers, 
    plannerModels, 
    formatterModels, 
    currentPlannerProvider, 
    currentPlannerModel, 
    plannerTimeout,
    currentFormatterProvider, 
    currentFormatterModel, 
    formatterTimeout, 
    updateConfig,
    providerStatus 
  } = useModels();
  
  const [timeoutInput, setTimeoutInput] = useState<string>("59");
  const [timeoutError, setTimeoutError] = useState<string | null>(null);

  useEffect(() => {
    setTimeoutInput(formatterTimeout.toString());
  }, [formatterTimeout]);

  // Keep useChatStream in sync with UI models/providers changes
  useEffect(() => {
    updateStreamConfig({
      plannerProvider: currentPlannerProvider,
      plannerModel: currentPlannerModel,
      plannerTimeout: plannerTimeout,
      formatterProvider: currentFormatterProvider,
      formatterModel: currentFormatterModel,
      formatterTimeout: formatterTimeout
    });
  }, [
    currentPlannerProvider, 
    currentPlannerModel, 
    plannerTimeout, 
    currentFormatterProvider, 
    currentFormatterModel, 
    formatterTimeout, 
    updateStreamConfig
  ]);

  const handleApplyTimeout = () => {
    const val = parseFloat(timeoutInput);
    if (isNaN(val) || val < 5 || val > 300) {
      setTimeoutError("5-300s");
      return;
    }
    setTimeoutError(null);
    updateConfig({ planner_timeout: val, formatter_timeout: val });
  };

  const handleFileSelect = async (file: File) => {
    const res = await uploadExperiment(file);
    if (res && res.comparisons && res.comparisons.length > 0) {
      const report = res.comparisons[0];
      
      // Inject system message with comparison results
      addCustomMessage({
        id: crypto.randomUUID(),
        role: "system",
        content: `Uploaded experiment: ${file.name}`,
        uploadResult: report,
      });

      // Trigger assistant explanation
      sendMessage(
        `I just uploaded an experiment (${file.name}). Please summarize the comparison results and tell me if the conditions look optimal.`,
        report,
        "upload_comparison"
      );
    }
  };

  const plannerStatus = providerStatus[currentPlannerProvider];
  const formatterStatus = providerStatus[currentFormatterProvider];

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b border-border bg-card px-6 py-4 flex flex-col sm:flex-row items-center justify-between shadow-sm z-10 gap-4">
        <h1 className="text-xl font-bold tracking-tight">ORD Assistant</h1>
        
        <div className="flex flex-wrap items-center gap-4 justify-center sm:justify-end">
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground font-semibold">Planner:</label>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none w-24"
              value={currentPlannerProvider}
              onChange={(e) => updateConfig({ planner_provider: e.target.value })}
            >
              <option value="loading..." disabled>provider...</option>
              {providers.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none max-w-[120px] sm:max-w-none"
              value={currentPlannerModel}
              onChange={(e) => updateConfig({ planner_model: e.target.value })}
              disabled={plannerStatus?.available === false}
            >
              <option value="loading..." disabled>model...</option>
              {plannerModels.map(m => <option key={m} value={m} title={m}>{m.length > 20 ? m.substring(0, 17) + '...' : m}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-muted-foreground font-semibold">Formatter:</label>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none w-24"
              value={currentFormatterProvider}
              onChange={(e) => updateConfig({ formatter_provider: e.target.value })}
            >
              <option value="loading..." disabled>provider...</option>
              {providers.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <select 
              className="text-sm bg-secondary text-secondary-foreground border border-border rounded px-2 py-1 outline-none max-w-[120px] sm:max-w-none"
              value={currentFormatterModel}
              onChange={(e) => updateConfig({ formatter_model: e.target.value })}
              disabled={formatterStatus?.available === false}
            >
              <option value="loading..." disabled>model...</option>
              {formatterModels.map(m => <option key={m} value={m} title={m}>{m.length > 20 ? m.substring(0, 17) + '...' : m}</option>)}
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
          <div className="text-xs text-muted-foreground font-mono ml-2 hidden xl:block">Experimental Engine V1</div>
        </div>
      </header>
      
      {(plannerStatus?.available === false || formatterStatus?.available === false) && (
        <div className="bg-destructive/10 text-destructive px-6 py-2 text-xs flex items-center justify-between">
          <span>
            <strong>Provider Unavailable: </strong> 
            {plannerStatus?.available === false && `Planner (${currentPlannerProvider}): ${plannerStatus.error} `}
            {formatterStatus?.available === false && currentFormatterProvider !== currentPlannerProvider && `Formatter (${currentFormatterProvider}): ${formatterStatus.error}`}
          </span>
        </div>
      )}

      <main className="flex-1 flex flex-col min-h-0 relative">
        <ChatStream messages={messages} onSuggestion={(q) => { if (!isGenerating) sendMessage(q); }} />
        <div className="shrink-0 relative">
          {uploadState !== "idle" && uploadedFile && (
            <UploadPreview 
              file={uploadedFile}
              progress={uploadProgress}
              state={uploadState}
              error={uploadError}
              onCancel={cancelUpload}
            />
          )}
          <ChatInput 
            onSendMessage={sendMessage} 
            onFileSelect={handleFileSelect}
            disabled={isGenerating || uploadState === "uploading"} 
          />
        </div>
      </main>
    </div>
  );
}
