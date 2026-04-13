"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
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
import { useResumeWorkflow } from "@/hooks/use-resume-workflow";

export function ResumeUploadPanel() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const mutation = useResumeWorkflow();

  const onSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!file) return;
      mutation.mutate(file, {
        onSuccess: (data) => {
          router.push(`/analysis/${data.analysis_id}`);
        },
      });
    },
    [file, mutation, router],
  );

  return (
    <Card className="mx-auto max-w-xl">
      <CardHeader>
        <CardTitle>Upload resume</CardTitle>
        <CardDescription>
          PDF or DOCX. We parse it, run structured analysis, and store results
          for chat and reports.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="space-y-2">
            <Label htmlFor="resume">File</Label>
            <Input
              id="resume"
              type="file"
              accept=".pdf,.doc,.docx,application/pdf"
              onChange={(ev) => {
                const f = ev.target.files?.[0];
                setFile(f ?? null);
              }}
            />
          </div>
          {mutation.isError ? (
            <Alert variant="destructive">
              <AlertTitle>Upload failed</AlertTitle>
              <AlertDescription>
                {mutation.error instanceof Error
                  ? mutation.error.message
                  : "Unknown error"}
              </AlertDescription>
            </Alert>
          ) : null}
          <Button type="submit" disabled={!file || mutation.isPending}>
            {mutation.isPending ? "Analyzing…" : "Upload & analyze"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
