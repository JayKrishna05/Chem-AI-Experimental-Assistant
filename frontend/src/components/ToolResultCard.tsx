import { useState } from "react";
import { ChevronDown, ChevronUp, Copy, Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface ToolResultCardProps {
  toolName: string;
  filters?: Record<string, unknown>;
  rawData: unknown;
}

export function ToolResultCard({ toolName, filters, rawData }: ToolResultCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!rawData) return null;

  const resultCount = Array.isArray(rawData) ? rawData.length : Object.keys(rawData).length;
  
  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(JSON.stringify(rawData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="mt-2 text-sm bg-card border-border overflow-hidden">
      <CardHeader 
        className="p-3 bg-muted/50 flex flex-row items-center justify-between cursor-pointer space-y-0"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2 m-0">
            {toolName} 
            <span className="text-xs text-muted-foreground font-normal">({resultCount} results)</span>
          </CardTitle>
        </div>
        {isOpen ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      
      {isOpen && (
        <CardContent className="p-0 flex flex-col">
          {filters && Object.keys(filters).length > 0 && (
            <div className="p-3 border-b border-border bg-muted/20">
              <span className="text-xs font-semibold uppercase text-muted-foreground">Filters: </span>
              <span className="font-mono text-xs text-foreground/80">{JSON.stringify(filters)}</span>
            </div>
          )}
          
          <div className="relative group p-3 bg-background overflow-auto max-h-96">
            <Button
              variant="outline"
              size="icon"
              className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity bg-background"
              onClick={handleCopy}
              title="Copy JSON"
            >
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>
            <pre className="text-xs font-mono">
              <code>{JSON.stringify(rawData, null, 2)}</code>
            </pre>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
