import type { AnalyzeResumeResponse } from "@/types/analysis";

const KEY = "mycareer_analyses_v1";
const MAX = 30;

export type CachedAnalysis = {
  analysisId: string;
  resumeId: string;
  summaryPreview: string;
  resumeScore?: number;
  atsScore?: number;
  savedAt: string;
  payload?: AnalyzeResumeResponse;
};

function read(): CachedAnalysis[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const v = JSON.parse(raw) as CachedAnalysis[];
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

function write(items: CachedAnalysis[]) {
  localStorage.setItem(KEY, JSON.stringify(items.slice(0, MAX)));
}

export function cacheAnalysisResult(res: AnalyzeResumeResponse) {
  const list = read();
  const entry: CachedAnalysis = {
    analysisId: res.analysis_id,
    resumeId: res.resume_id,
    summaryPreview: res.summary.slice(0, 160),
    resumeScore: res.analysis?.resume_score,
    atsScore: res.analysis?.ats_compatibility?.score,
    savedAt: new Date().toISOString(),
    payload: res,
  };
  const next = [
    entry,
    ...list.filter((x) => x.analysisId !== res.analysis_id),
  ].slice(0, MAX);
  write(next);
}

export function listCachedAnalyses(): CachedAnalysis[] {
  return read();
}

export function getCachedAnalysis(analysisId: string): CachedAnalysis | null {
  return read().find((x) => x.analysisId === analysisId) ?? null;
}
