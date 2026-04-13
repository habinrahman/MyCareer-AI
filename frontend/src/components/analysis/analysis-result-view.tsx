"use client";

import { useMutation } from "@tanstack/react-query";
import type { AnalyzeResumeResponse } from "@/types/analysis";
import { downloadAnalysisPdf } from "@/lib/api/chat";
import { downloadBlob } from "@/lib/download-blob";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

function ListBlock({
  title,
  items,
}: {
  title?: string;
  items?: string[];
}) {
  if (!items?.length) return null;
  return (
    <div>
      {title ? (
        <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      ) : null}
      <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
        {items.map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
    </div>
  );
}

export function AnalysisResultView({ data }: { data: AnalyzeResumeResponse }) {
  const a = data.analysis;
  const pdf = useMutation({
    mutationFn: () => downloadAnalysisPdf(data.analysis_id),
    onSuccess: (blob) => {
      downloadBlob(
        blob,
        `mycareer-report-${data.analysis_id.slice(0, 8)}.pdf`,
      );
    },
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">Analysis</h1>
            <Badge variant="secondary">v{data.analysis_version}</Badge>
          </div>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {data.analysis_id}
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="shrink-0"
          disabled={pdf.isPending}
          onClick={() => pdf.mutate()}
        >
          {pdf.isPending ? "Preparing PDF…" : "Download PDF"}
        </Button>
      </div>
      {pdf.isError ? (
        <p className="text-sm text-destructive">
          {pdf.error instanceof Error ? pdf.error.message : "Download failed"}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Executive summary</CardTitle>
          <CardDescription>High-level read from your resume</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed">
          <p>{data.summary}</p>
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            {a.resume_score != null ? (
              <span>
                Resume score:{" "}
                <strong className="text-foreground">{a.resume_score}</strong>
              </span>
            ) : null}
            {a.ats_compatibility?.score != null ? (
              <span>
                ATS fit:{" "}
                <strong className="text-foreground">
                  {a.ats_compatibility.score}
                </strong>
              </span>
            ) : null}
            <span>Parsed ~{data.parsed_char_count.toLocaleString()} chars</span>
          </div>
        </CardContent>
      </Card>

      {a.professional_summary ? (
        <Card>
          <CardHeader>
            <CardTitle>Professional summary</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-relaxed">
            {a.professional_summary}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Strengths & gaps</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ListBlock title="Strengths" items={a.strengths} />
            <Separator />
            <ListBlock title="Weaknesses" items={a.weaknesses} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ATS & skills</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {a.ats_compatibility ? (
              <div>
                <p className="font-medium">ATS compatibility</p>
                {a.ats_compatibility.formatting_notes ? (
                  <p className="mt-1 text-muted-foreground">
                    {a.ats_compatibility.formatting_notes}
                  </p>
                ) : null}
                <ListBlock
                  title="Keyword matches"
                  items={a.ats_compatibility.keywords_match}
                />
                <ListBlock
                  title="Suggestions"
                  items={a.ats_compatibility.suggestions}
                />
              </div>
            ) : null}
            {a.skills_assessment ? (
              <div>
                <p className="font-medium">Skills</p>
                <ListBlock
                  title="Technical"
                  items={a.skills_assessment.technical_skills}
                />
                <ListBlock
                  title="Soft skills"
                  items={a.skills_assessment.soft_skills}
                />
                {a.skills_assessment.proficiency_notes ? (
                  <p className="mt-2 text-muted-foreground">
                    {a.skills_assessment.proficiency_notes}
                  </p>
                ) : null}
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      {a.skill_gap_analysis?.gaps?.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Skill gaps</CardTitle>
            {a.skill_gap_analysis.industry_context ? (
              <CardDescription>
                {a.skill_gap_analysis.industry_context}
              </CardDescription>
            ) : null}
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {a.skill_gap_analysis.gaps.map((g) => (
              <div
                key={g.skill}
                className="rounded-md border bg-muted/40 p-3"
              >
                <p className="font-medium">{g.skill}</p>
                {g.gap_description ? (
                  <p className="mt-1 text-muted-foreground">{g.gap_description}</p>
                ) : null}
                {g.importance ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Importance: {g.importance}
                  </p>
                ) : null}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recommended roles</CardTitle>
          </CardHeader>
          <CardContent>
            {a.recommended_roles?.length ? (
              <ListBlock items={a.recommended_roles} />
            ) : (
              <p className="text-sm text-muted-foreground">No roles listed.</p>
            )}
          </CardContent>
        </Card>
        {a.career_outlook ? (
          <Card>
            <CardHeader>
              <CardTitle>Career outlook</CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-relaxed">
              {a.career_outlook}
            </CardContent>
          </Card>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Improvements</CardTitle>
        </CardHeader>
        <CardContent>
          {a.improvement_suggestions?.length ? (
            <ListBlock items={a.improvement_suggestions} />
          ) : (
            <p className="text-sm text-muted-foreground">No suggestions.</p>
          )}
        </CardContent>
      </Card>

      {a.course_recommendations?.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Learning picks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {a.course_recommendations.map((c) => (
              <div key={c.title} className="rounded-md border p-3 text-sm">
                <p className="font-medium">{c.title}</p>
                {c.provider ? (
                  <p className="text-xs text-muted-foreground">{c.provider}</p>
                ) : null}
                {c.rationale ? (
                  <p className="mt-2 text-muted-foreground">{c.rationale}</p>
                ) : null}
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
