import { useState, KeyboardEvent, useRef } from "react";
import { SendHorizontal, Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { UploadDropzone } from "./UploadDropzone";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onFileSelect: (file: File) => void;
  disabled: boolean;
}

export function ChatInput({ onSendMessage, onFileSelect, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [showDropzone, setShowDropzone] = useState(false);

  const handleSend = () => {
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (file: File) => {
    setShowDropzone(false);
    onFileSelect(file);
  };

  return (
    <div className="relative flex gap-2 p-4 bg-background border-t border-border">
      {showDropzone && (
        <UploadDropzone 
          onFileSelect={handleFileSelect}
          onClose={() => setShowDropzone(false)}
        />
      )}
      <Button 
        onClick={() => setShowDropzone((prev) => !prev)} 
        disabled={disabled}
        size="icon"
        variant={showDropzone ? "secondary" : "ghost"}
        className="text-muted-foreground"
      >
        <Paperclip className="h-5 w-5" />
      </Button>
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about the ORD datasets..."
        disabled={disabled}
        className="flex-1"
      />
      <Button 
        onClick={handleSend} 
        disabled={disabled || !input.trim()}
        size="icon"
      >
        <SendHorizontal className="h-5 w-5" />
      </Button>
    </div>
  );
}
