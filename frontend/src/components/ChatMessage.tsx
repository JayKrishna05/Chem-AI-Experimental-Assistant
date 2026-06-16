import { useState } from "react";
import { ChatMessage as ChatMessageType } from "@/types/chat";
import { ToolResultCard } from "./ToolResultCard";
import { StatusIndicator } from "./StatusIndicator";
import { Copy, Check } from "lucide-react";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex flex-col mb-6 ${isUser ? "items-end" : "items-start"}`}>
      <div 
        className={`max-w-[85%] rounded-lg p-4 relative group ${
          isUser 
            ? "bg-primary text-primary-foreground" 
            : "bg-muted text-foreground border border-border"
        }`}
      >
        <div className="text-sm whitespace-pre-wrap leading-relaxed pr-6 max-h-[60vh] overflow-y-auto">
          {message.content}
        </div>
        
        {!isUser && message.content && (
          <button 
            onClick={handleCopy}
            className="absolute top-2 right-2 text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity"
            title="Copy message"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
          </button>
        )}
        
        {!isUser && message.status && !["idle", "done", "error", "no_tool"].includes(message.status) && (
          <StatusIndicator status={message.status} />
        )}
        
        {!isUser && message.errorMessage && (
          <div className="text-destructive text-sm mt-2 font-medium">
            Error: {message.errorMessage}
          </div>
        )}

        {!isUser && message.rawData !== undefined && message.toolName && (
          <ToolResultCard 
            toolName={message.toolName} 
            filters={message.filters} 
            rawData={message.rawData} 
          />
        )}
      </div>
    </div>
  );
}
