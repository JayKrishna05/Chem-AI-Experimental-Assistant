import { useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { useChatStream } from "@/hooks/useChatStream";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ChatStreamProps {
  messages: ReturnType<typeof useChatStream>["messages"];
  onSuggestion?: (query: string) => void;
}

const SUGGESTIONS = [
  { label: "Database summary", query: "Summarize the database" },
  { label: "Buchwald-Hartwig", query: "Find Buchwald-Hartwig reactions" },
  { label: "Palladium catalysts", query: "Most common catalysts in Buchwald-Hartwig reactions" },
  { label: "Yield statistics", query: "Show yield statistics" },
  { label: "Temperature statistics", query: "Show temperature statistics" },
  { label: "Dataset coverage", query: "Which datasets contain the most reactions?" },
  { label: "Reaction types", query: "What reaction types are available?" },
  { label: "Procedures with palladium", query: "Show procedures mentioning palladium" },
  { label: "Boronic acid reactions", query: "Find reactions involving boronic acids" },
  { label: "Most common solvents", query: "What solvents are most commonly used?" },
];

export function ChatStream({ messages, onSuggestion }: ChatStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="flex flex-col max-w-4xl mx-auto w-full pb-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center mt-12 gap-6 text-center px-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-2xl">⚗️</span>
              </div>
              <div className="text-left">
                <h2 className="text-xl font-bold text-foreground">ORD Experimental Intelligence</h2>
                <p className="text-sm text-muted-foreground">Search reactions, procedures, molecules, and trends</p>
              </div>
            </div>
            <p className="text-muted-foreground text-sm max-w-md">
              Explore <strong>2.4 million reactions</strong>, <strong>1.8 million procedures</strong>, and{" "}
              <strong>2 million molecules</strong> from the Open Reaction Database.
            </p>
            <div className="w-full max-w-2xl">
              <p className="text-xs text-muted-foreground uppercase font-semibold tracking-wider mb-3">Try asking...</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.query}
                    onClick={() => onSuggestion?.(s.query)}
                    className="text-xs px-3 py-1.5 rounded-full border border-border bg-secondary hover:bg-secondary/80 text-secondary-foreground transition-colors"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
