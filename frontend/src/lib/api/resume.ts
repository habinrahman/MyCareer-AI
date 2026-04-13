import { apiClient } from "@/lib/api";
import type { AnalyzeResumeResponse } from "@/types/analysis";

export type UploadResumeResponse = {
  resume_id: string;
  storage_path: string;
  original_filename: string;
  mime_type?: string | null;
  file_size_bytes: number;
};

export async function uploadResumeApi(file: File): Promise<UploadResumeResponse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<UploadResumeResponse>(
    "/upload-resume",
    form,
  );
  return data;
}

export async function analyzeResumeApi(
  resumeId: string,
): Promise<AnalyzeResumeResponse> {
  const { data } = await apiClient.post<AnalyzeResumeResponse>(
    "/analyze-resume",
    { resume_id: resumeId },
  );
  return data;
}
