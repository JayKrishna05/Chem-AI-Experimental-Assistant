import React from "react";
import { X, File as FileIcon, UploadCloud, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { UploadState } from "@/hooks/useUpload";

interface UploadPreviewProps {
  file: File;
  progress: number;
  state: UploadState;
  error: string | null;
  onCancel: () => void;
}

export function UploadPreview({ file, progress, state, error, onCancel }: UploadPreviewProps) {
  const extension = file.name.split(".").pop()?.toUpperCase() || "FILE";
  const sizeMb = (file.size / (1024 * 1024)).toFixed(2);

  return (
    <div className="absolute bottom-full mb-2 left-0 right-0 z-50 p-4 bg-card border rounded-lg shadow-lg">
      <div className="flex items-center gap-3">
        <div className="bg-primary/10 p-2 rounded flex-shrink-0">
          <FileIcon className="h-6 w-6 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium truncate">{file.name}</h4>
          <p className="text-xs text-muted-foreground">{extension} • {sizeMb} MB</p>
        </div>
        <div className="flex-shrink-0">
          {state === "idle" || state === "uploading" ? (
            <Button variant="ghost" size="icon-sm" onClick={onCancel} title="Cancel upload">
              <X className="h-4 w-4" />
            </Button>
          ) : state === "success" ? (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          ) : (
            <Button variant="ghost" size="icon-sm" onClick={onCancel}>
              <X className="h-4 w-4 text-destructive" />
            </Button>
          )}
        </div>
      </div>

      <div className="mt-3">
        {state === "uploading" && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span>Parsing and comparing... {progress}%</span>
          </div>
        )}
        
        {state === "error" && (
          <div className="flex items-center gap-2 text-xs text-destructive mb-1">
            <AlertCircle className="h-3 w-3" />
            <span>{error || "Upload failed"}</span>
          </div>
        )}

        {(state === "uploading" || state === "success") && (
          <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-300 ${state === "success" ? "bg-green-500" : "bg-primary"}`}
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
