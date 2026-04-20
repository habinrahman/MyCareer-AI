"use client";

import { useCallback, useState } from "react";
import { Download, FileText, Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LearningPaths } from "@/components/resume/LearningPaths";
import { getApiBaseUrl } from "@/lib/api";

export type PublicAnalyzeResponse = {
  summary: string;
  parsed_char_count: number;
  scores: {
    resume_score: number;
    ats_score: number;
    model: string;
    prompt_version: string;
  };
  analysis: {
    strengths: string[];
    weaknesses: string[];
    improvement_suggestions: string[];
    recommended_roles: string[];
    skill_gap_analysis: {
      gaps: Array<{ skill: string; gap_description: string; importance: string }>;
      industry_context: string;
    };
    ats_compatibility: {
      score: number;
      keywords_match: string[];
      formatting_notes: string;
      suggestions: string[];
    };
    course_recommendations: Array<{ title: string; provider?: string | null; rationale: string }>;
  };
};

function ListBlock({ title, items }: { title: string; items: string[] }) {
  if (!items?.length) return null;
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-foreground">{title}</h3>
      <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
        {items.map((item, i) => (
          <li key={`${i}-${item.slice(0, 48)}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export function ResumeUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [drag, setDrag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PublicAnalyzeResponse | null>(null);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f && (f.name.toLowerCase().endsWith(".pdf") || f.name.toLowerCase().endsWith(".docx"))) {
      setFile(f);
      setError(null);
      setResult(null);
    } else {
      setError("Please upload a PDF or DOCX file.");
    }
  }, []);

  const analyze = async () => {
    if (!file) {
      setError("Choose a resume file first.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    const API_URL = getApiBaseUrl();
    const formData = new FormData();
    formData.append("file", file);
    try {
      console.log("Sending request…", { API_URL, filename: file.name });
      const response = await fetch(`${API_URL}/public/analyze-resume?format=json`, {
        method: "POST",
        body: formData,
      });
      console.log("Response received:", response);

      if (!response.ok) {
        let detail: string | undefined;
        try {
          const errBody = (await response.json()) as { detail?: unknown };
          if (typeof errBody.detail === "string") detail = errBody.detail;
        } catch {
          /* body not JSON */
        }
        setError(detail ?? `Request failed (${response.status}).`);
        return;
      }

      const data = (await response.json()) as PublicAnalyzeResponse;
      setResult(data);
    } catch (e) {
      console.error("API ERROR:", e);
      setError("Something went wrong while analyzing resume.");
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = async () => {
    if (!file) return;
    setPdfLoading(true);
    setError(null);
    const API_URL = getApiBaseUrl();
    const formData = new FormData();
    formData.append("file", file);
    try {
      console.log("Sending request…", { API_URL, format: "pdf", filename: file.name });
      const response = await fetch(`${API_URL}/public/analyze-resume?format=pdf`, {
        method: "POST",
        body: formData,
      });
      console.log("Response received:", response);

      if (!response.ok) {
        let msg = "Could not generate PDF. Try analyzing again first.";
        try {
          const errBody = (await response.json()) as { detail?: unknown };
          if (typeof errBody.detail === "string") msg = errBody.detail;
        } catch {
          /* not JSON */
        }
        setError(msg);
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${file.name.replace(/\.[^.]+$/, "")}-review.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("API ERROR:", e);
      setError("Something went wrong while generating the PDF.");
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <Card
        className={`border-2 border-dashed transition-colors ${drag ? "border-primary bg-primary/5" : "border-muted"}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Upload className="h-5 w-5" />
            Upload resume
          </CardTitle>
          <CardDescription>
            PDF or DOCX, up to your API limit. No account required — results are not stored.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <input
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-primary-foreground"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  setFile(f);
                  setError(null);
                  setResult(null);
                }
              }}
            />
            <Button type="button" onClick={() => void analyze()} disabled={loading || !file}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing…
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Get instant feedback
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => void downloadPdf()}
              disabled={pdfLoading || !file}
            >
              {pdfLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              PDF report
            </Button>
          </div>
          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}
        </CardContent>
      </Card>

      {result ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Resume score</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold tabular-nums">{result.scores.resume_score}</p>
                <p className="text-xs text-muted-foreground">Overall quality (model estimate)</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">ATS score</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold tabular-nums">{result.scores.ats_score}</p>
                <p className="text-xs text-muted-foreground">Applicant tracking alignment</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">{result.summary}</p>
              <p className="mt-3 text-xs text-muted-foreground">
                Parsed {result.parsed_char_count.toLocaleString()} characters
              </p>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Strengths & gaps</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ListBlock title="Strengths" items={result.analysis.strengths} />
                <ListBlock title="Weaknesses" items={result.analysis.weaknesses} />
                {result.analysis.skill_gap_analysis?.gaps?.length ? (
                  <div>
                    <h3 className="mb-2 text-sm font-semibold">Skill gaps</h3>
                    <ul className="space-y-2 text-sm text-muted-foreground">
                      {result.analysis.skill_gap_analysis.gaps.map((g) => (
                        <li key={g.skill} className="rounded-md border bg-card/50 p-2">
                          <span className="font-medium text-foreground">{g.skill}</span>
                          <span className="text-xs uppercase text-muted-foreground">
                            {" "}
                            · {g.importance}
                          </span>
                          {g.gap_description ? (
                            <p className="mt-1">{g.gap_description}</p>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Suggestions & roles</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ListBlock
                  title="Actionable improvements"
                  items={result.analysis.improvement_suggestions}
                />
                <ListBlock title="Recommended roles" items={result.analysis.recommended_roles} />
                {result.analysis.ats_compatibility?.suggestions?.length ? (
                  <ListBlock
                    title="ATS formatting & keywords"
                    items={[
                      ...(result.analysis.ats_compatibility.formatting_notes
                        ? [result.analysis.ats_compatibility.formatting_notes]
                        : []),
                      ...result.analysis.ats_compatibility.suggestions,
                    ]}
                  />
                ) : null}
                <LearningPaths
                  paths={result.analysis.course_recommendations ?? []}
                  className="mt-6 border-t border-border pt-4"
                />
              </CardContent>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}
