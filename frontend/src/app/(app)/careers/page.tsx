"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
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

type CareerMe = { role: "student" };

type BenchmarkComparison = {
  benchmark_id: string;
  industry: string;
  role_family: string;
  metric_name: string;
  p25: number | null;
  p50: number;
  p75: number | null;
  user_value: number | null;
  band: string | null;
  narrative: string | null;
};

type BenchmarksResponse = {
  resume_id: string | null;
  analysis_id: string | null;
  comparisons: BenchmarkComparison[];
  notes: string[];
};

type JobMatchRow = {
  job_id: string;
  title: string;
  company_name: string | null;
  location: string | null;
  similarity: number | null;
  external_url: string | null;
};

type JobMatchResponse = {
  resume_id: string;
  query_source: string;
  matches: JobMatchRow[];
  fallback_text_only: boolean;
  notes: string[];
};

export default function CareersPage() {
  const [me, setMe] = useState<CareerMe | null>(null);
  const [loadingMe, setLoadingMe] = useState(true);
  const [industry, setIndustry] = useState("Software");
  const [roleFamily, setRoleFamily] = useState("Backend Engineer");
  const [benchmarks, setBenchmarks] = useState<BenchmarksResponse | null>(null);
  const [benchLoading, setBenchLoading] = useState(false);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchResult, setMatchResult] = useState<JobMatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadMe = useCallback(async () => {
    setLoadingMe(true);
    setError(null);
    try {
      const { data } = await apiClient.get<CareerMe>("/careers/me");
      setMe(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load profile");
    } finally {
      setLoadingMe(false);
    }
  }, []);

  useEffect(() => {
    void loadMe();
  }, [loadMe]);

  async function loadBenchmarks() {
    setBenchLoading(true);
    setError(null);
    try {
      const { data } = await apiClient.get<BenchmarksResponse>("/careers/benchmarks", {
        params: {
          industry: industry || undefined,
          role_family: roleFamily || undefined,
        },
      });
      setBenchmarks(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Benchmarks failed");
    } finally {
      setBenchLoading(false);
    }
  }

  async function runJobMatch() {
    setMatchLoading(true);
    setError(null);
    setMatchResult(null);
    try {
      const { data } = await apiClient.post<JobMatchResponse>("/careers/jobs/match", {
        limit: 12,
        backfill_job_embeddings: true,
      });
      setMatchResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Job match failed");
    } finally {
      setMatchLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Career insights</h1>
        <p className="mt-2 text-muted-foreground">
          Resume intelligence for your student dashboard: industry benchmarks, semantic job
          examples for learning (not placement), and links to your AI mentor.
        </p>
      </div>

      {error ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Student dashboard</CardTitle>
          <CardDescription>
            Profile settings (name, email, and linked accounts) live under Account. Your workspace
            role is always <span className="font-medium text-foreground">student</span>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loadingMe || !me ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-muted-foreground">
                Role: <span className="font-medium text-foreground">{me.role}</span>
              </p>
              <Button asChild variant="outline" size="sm">
                <Link href="/settings">Open profile settings</Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>AI mentor</CardTitle>
          <CardDescription>
            Personalized career guidance grounded in your resume and analyses.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/chat">Open mentor chat</Link>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Industry benchmarking</CardTitle>
          <CardDescription>
            Compare your latest AI resume score to reference cohorts (seed data is illustrative).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input
                id="industry"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="Software"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role family</Label>
              <Input
                id="role"
                value={roleFamily}
                onChange={(e) => setRoleFamily(e.target.value)}
                placeholder="Backend Engineer"
              />
            </div>
          </div>
          <Button type="button" onClick={() => void loadBenchmarks()} disabled={benchLoading}>
            {benchLoading ? "Loading…" : "Load benchmarks"}
          </Button>
          {benchmarks ? (
            <div className="space-y-3 text-sm">
              {benchmarks.notes.map((n) => (
                <p key={n} className="text-muted-foreground">
                  {n}
                </p>
              ))}
              {benchmarks.comparisons.map((c) => (
                <div key={c.benchmark_id} className="rounded-md border bg-card/50 p-3">
                  <p className="font-medium">
                    {c.industry} · {c.role_family}
                  </p>
                  <p className="text-muted-foreground">
                    p25 {c.p25 ?? "—"} · median {c.p50} · p75 {c.p75 ?? "—"}
                    {c.user_value != null ? ` · yours: ${c.user_value}` : ""}
                  </p>
                  {c.band ? <p className="mt-1 text-xs uppercase text-muted-foreground">{c.band}</p> : null}
                  {c.narrative ? <p className="mt-2">{c.narrative}</p> : null}
                </div>
              ))}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>AI job matching (learning)</CardTitle>
          <CardDescription>
            Surfaces roles that are semantically close to your resume so you can study gaps,
            keywords, and project ideas. This is not a hiring or placement workflow.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button type="button" onClick={() => void runJobMatch()} disabled={matchLoading}>
            {matchLoading ? "Matching…" : "Match jobs to my resume"}
          </Button>
          {matchResult ? (
            <div className="space-y-2 text-sm">
              <p className="text-muted-foreground">
                Resume {matchResult.resume_id} · {matchResult.query_source}
                {matchResult.fallback_text_only ? " · text fallback" : ""}
              </p>
              {matchResult.notes.map((n) => (
                <p key={n} className="text-muted-foreground">
                  {n}
                </p>
              ))}
              <ul className="space-y-2">
                {matchResult.matches.map((m) => (
                  <li key={m.job_id} className="rounded-md border p-3">
                    <p className="font-medium">{m.title}</p>
                    <p className="text-muted-foreground">
                      {[m.company_name, m.location].filter(Boolean).join(" · ")}
                      {m.similarity != null ? ` · score ${m.similarity.toFixed(3)}` : ""}
                    </p>
                    {m.external_url ? (
                      <a
                        className="text-xs text-primary underline"
                        href={m.external_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Link
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
