import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 to-background">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-4 py-6 sm:px-6">
        <span className="text-lg font-semibold tracking-tight">MyCareer AI</span>
        <div className="flex gap-2">
          <Button variant="ghost" asChild>
            <Link href="/auth/login">Log in</Link>
          </Button>
          <Button asChild>
            <Link href="/auth/signup">Get started</Link>
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 pb-24 pt-12 sm:px-6 sm:pt-16">
        <p className="text-sm font-medium uppercase tracking-wide text-brand-600">
          Resume intelligence
        </p>
        <h1 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          Turn your resume into a clear career plan
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-muted-foreground">
          Structured analysis, ATS-aware feedback, an AI mentor that remembers
          your CV, and branded PDF reports — powered by your stack and Supabase
          auth.
        </p>
        <div className="mt-10 flex flex-wrap gap-3">
          <Button size="lg" asChild>
            <Link href="/auth/signup">Create account</Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/auth/login">I already have an account</Link>
          </Button>
        </div>

        <div className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Deep resume analysis</CardTitle>
              <CardDescription>
                Scores, strengths, gaps, and learning suggestions in one pass.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Streaming mentor chat</CardTitle>
              <CardDescription>
                RAG-grounded answers with session history and persistence.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card className="sm:col-span-2 lg:col-span-1">
            <CardHeader>
              <CardTitle>Downloadable reports</CardTitle>
              <CardDescription>
                Export polished PDF reports for the analyses you own.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </main>
    </div>
  );
}
