import { ChatMessage as ChatMessageType } from "@/types/chat";
import { ToolResultCard } from "./ToolResultCard";
import { StatusIndicator } from "./StatusIndicator";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex flex-col mb-6 ${isUser ? "items-end" : "items-start"}`}>
      <div 
        className={`max-w-[85%] rounded-lg p-4 ${
          isUser 
            ? "bg-primary text-primary-foreground" 
            : "bg-muted text-foreground border border-border"
        }`}
      >
        <div className="text-sm whitespace-pre-wrap leading-relaxed">
          {message.content}
        </div>
        
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
