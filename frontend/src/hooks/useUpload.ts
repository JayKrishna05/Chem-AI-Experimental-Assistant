import { useState, useCallback } from "react";
import { uploadAndCompareExperiment, CompareExperimentResponse } from "@/services/upload";

export type UploadState = "idle" | "uploading" | "success" | "error";

export function useUpload() {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const uploadExperiment = useCallback(async (file: File): Promise<CompareExperimentResponse | null> => {
    setUploadState("uploading");
    setUploadProgress(0);
    setUploadError(null);
    setUploadedFile(file);

    try {
      // Simulate progress since fetch doesn't support true upload progress natively
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const response = await uploadAndCompareExperiment(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadState("success");
      
      return response;
    } catch (error) {
      setUploadState("error");
      setUploadError(error instanceof Error ? error.message : "Unknown error");
      return null;
    } finally {
      setTimeout(() => {
        setUploadState("idle");
        setUploadProgress(0);
        setUploadError(null);
        setUploadedFile(null);
      }, 3000);
    }
  }, []);

  const cancelUpload = useCallback(() => {
    // In a real app we might abort the fetch request using AbortController
    setUploadState("idle");
    setUploadProgress(0);
    setUploadError(null);
    setUploadedFile(null);
  }, []);

  return {
    uploadExperiment,
    cancelUpload,
    uploadProgress,
    uploadedFile,
    uploadState,
    uploadError,
  };
}
