"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AnalysisResultView } from "@/components/analysis/analysis-result-view";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { getCachedAnalysis } from "@/lib/storage/analysis-cache";
import type { AnalyzeResumeResponse } from "@/types/analysis";

export default function AnalysisPage() {
  const params = useParams();
  const analysisId = params.analysisId as string;
  const [data, setData] = useState<AnalyzeResumeResponse | null>(null);

  useEffect(() => {
    const row = getCachedAnalysis(analysisId);
    setData(row?.payload ?? null);
  }, [analysisId]);

  if (!data) {
    return (
      <div className="mx-auto max-w-lg space-y-4">
        <Alert>
          <AlertTitle>Analysis not in browser cache</AlertTitle>
          <AlertDescription>
            Open an analysis right after it completes, or run a new upload from
            the resume page. (The API does not expose a public “get analysis by
            id” JSON route yet.)
          </AlertDescription>
        </Alert>
        <Button asChild>
          <Link href="/resume">Upload resume</Link>
        </Button>
      </div>
    );
  }

  return <AnalysisResultView data={data} />;
}
