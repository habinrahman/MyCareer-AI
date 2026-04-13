"use client";

import { useMutation } from "@tanstack/react-query";
import { analyzeResumeApi, uploadResumeApi } from "@/lib/api/resume";
import { cacheAnalysisResult } from "@/lib/storage/analysis-cache";

export function useResumeWorkflow() {
  return useMutation({
    mutationFn: async (file: File) => {
      const uploaded = await uploadResumeApi(file);
      const analyzed = await analyzeResumeApi(uploaded.resume_id);
      return analyzed;
    },
    onSuccess: (data) => {
      cacheAnalysisResult(data);
    },
  });
}
