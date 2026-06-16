import { AssistantStatus } from "@/types/chat";
import { Loader2 } from "lucide-react";

export function StatusIndicator({ status }: { status: AssistantStatus }) {
  let text = "";
  
  switch (status) {
    case "thinking":
      text = "Analyzing request...";
      break;
    case "tool_selected":
      text = "Running tool...";
      break;
    case "formatting":
      text = "Writing summary...";
      break;
    default:
      return null;
  }

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>{text}</span>
    </div>
  );
}
