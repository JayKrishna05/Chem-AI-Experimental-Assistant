import React, { useCallback, useState } from "react";
import { Upload, X, File as FileIcon } from "lucide-react";
import { Button } from "./ui/button";

interface UploadDropzoneProps {
  onFileSelect: (file: File) => void;
  onClose: () => void;
  allowedExtensions?: string[];
}

export function UploadDropzone({ onFileSelect, onClose, allowedExtensions = ["json", "csv", "xlsx"] }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        validateAndSelectFile(e.dataTransfer.files[0]);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSelectFile(e.target.files[0]);
    }
  };

  const validateAndSelectFile = (file: File) => {
    setError(null);
    const extension = file.name.split(".").pop()?.toLowerCase();
    
    if (!extension || !allowedExtensions.includes(extension)) {
      setError(`Invalid file type. Allowed: ${allowedExtensions.join(", ")}`);
      return;
    }
    
    // 10MB limit
    if (file.size > 10 * 1024 * 1024) {
      setError("File is too large (max 10MB).");
      return;
    }

    onFileSelect(file);
  };

  return (
    <div className="absolute bottom-full mb-2 left-0 right-0 z-50 p-4 bg-card border rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-semibold text-sm">Upload Experiment</h3>
        <Button variant="ghost" size="icon-sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div
        className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-lg transition-colors ${
          isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          onChange={handleChange}
          accept={allowedExtensions.map(ext => `.${ext}`).join(",")}
        />
        <Upload className={`h-8 w-8 mb-3 ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
        <p className="text-sm font-medium mb-1">
          Drag & drop a file here, or click to browse
        </p>
        <p className="text-xs text-muted-foreground">
          Supported formats: {allowedExtensions.map(e => e.toUpperCase()).join(", ")}
        </p>
      </div>

      {error && <p className="text-destructive text-xs mt-2">{error}</p>}
    </div>
  );
}
