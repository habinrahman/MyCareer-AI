"use client";

import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import { downloadAnalysisPdf } from "@/lib/api/chat";
import { fetchReportDetail } from "@/lib/api/reports";
import { downloadBlob } from "@/lib/download-blob";
import {
  listCachedAnalyses,
  type CachedAnalysis,
} from "@/lib/storage/analysis-cache";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function AnalysisRow({ row }: { row: CachedAnalysis }) {
  const dl = useMutation({
    mutationFn: () => downloadAnalysisPdf(row.analysisId),
    onSuccess: (blob) => {
      downloadBlob(blob, `mycareer-report-${row.analysisId.slice(0, 8)}.pdf`);
    },
  });

  return (
    <div className="flex flex-col gap-3 rounded-lg border bg-card p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <p className="truncate font-medium">{row.summaryPreview}…</p>
        <p className="mt-1 font-mono text-xs text-muted-foreground">
          {row.analysisId}
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          {row.resumeScore != null ? (
            <Badge variant="secondary">Score {row.resumeScore}</Badge>
          ) : null}
          {row.atsScore != null ? (
            <Badge variant="outline">ATS {row.atsScore}</Badge>
          ) : null}
        </div>
      </div>
      <div className="flex shrink-0 flex-wrap gap-2">
        <Button asChild variant="outline" size="sm">
          <Link href={`/analysis/${row.analysisId}`}>Open</Link>
        </Button>
        <Button
          type="button"
          size="sm"
          disabled={dl.isPending}
          onClick={() => dl.mutate()}
        >
          {dl.isPending ? "…" : "PDF"}
        </Button>
      </div>
      {dl.isError ? (
        <p className="w-full text-sm text-destructive">
          {dl.error instanceof Error ? dl.error.message : "Download failed"}
        </p>
      ) : null}
    </div>
  );
}

export function ReportsHub() {
  const [rows, setRows] = useState<CachedAnalysis[]>([]);
  const [reportId, setReportId] = useState("");

  const refreshList = useCallback(() => {
    setRows(listCachedAnalyses());
  }, []);

  useEffect(() => {
    refreshList();
  }, [refreshList]);

  const lookup = useMutation({
    mutationFn: () => fetchReportDetail(reportId.trim()),
  });

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Reports</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Download PDF reports for analyses you own. Stored report records can
          be opened by ID when your backend has created them.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent analyses (this browser)</CardTitle>
          <CardDescription>
            After each successful analysis we cache a snapshot locally so you
            can reopen results and download PDFs.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-end">
            <Button type="button" variant="outline" size="sm" onClick={refreshList}>
              Refresh list
            </Button>
          </div>
          {!rows.length ? (
            <p className="text-sm text-muted-foreground">
              No analyses yet.{" "}
              <Link href="/resume" className="text-primary underline">
                Upload a resume
              </Link>{" "}
              to generate one.
            </p>
          ) : (
            rows.map((row) => <AnalysisRow key={row.analysisId} row={row} />)
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Report by ID</CardTitle>
          <CardDescription>
            If you have a report UUID from the database, fetch metadata and a
            signed download URL when available.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="flex-1 space-y-2">
              <Label htmlFor="report-id">Report ID</Label>
              <Input
                id="report-id"
                placeholder="uuid…"
                value={reportId}
                onChange={(e) => setReportId(e.target.value)}
              />
            </div>
            <Button
              type="button"
              disabled={!reportId.trim() || lookup.isPending}
              onClick={() => lookup.mutate()}
            >
              {lookup.isPending ? "Loading…" : "Lookup"}
            </Button>
          </div>
          {lookup.isError ? (
            <Alert variant="destructive">
              <AlertTitle>Lookup failed</AlertTitle>
              <AlertDescription>
                {lookup.error instanceof Error
                  ? lookup.error.message
                  : "Unknown error"}
              </AlertDescription>
            </Alert>
          ) : null}
          {lookup.data ? (
            <div className="rounded-md border bg-muted/30 p-4 text-sm">
              <p>
                <span className="font-medium">Title:</span> {lookup.data.title}
              </p>
              <p className="mt-1">
                <span className="font-medium">Status:</span>{" "}
                {lookup.data.status}
              </p>
              <p className="mt-1">
                <span className="font-medium">Type:</span>{" "}
                {lookup.data.report_type}
              </p>
              {lookup.data.analysis_id ? (
                <p className="mt-1 font-mono text-xs">
                  Analysis: {lookup.data.analysis_id}
                </p>
              ) : null}
              {lookup.data.signed_url ? (
                <Button asChild className="mt-3" size="sm">
                  <a href={lookup.data.signed_url} target="_blank" rel="noreferrer">
                    Open signed URL
                  </a>
                </Button>
              ) : (
                <p className="mt-3 text-muted-foreground">
                  No signed URL (report may still be processing or not stored in
                  Supabase).
                </p>
              )}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
