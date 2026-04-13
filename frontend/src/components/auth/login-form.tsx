"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSession, useSupabaseConfigured } from "@/hooks/use-session";
import { safeNextPath } from "@/lib/auth/paths";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

const URL_ERROR_MESSAGES: Record<string, string> = {
  auth: "Email link or confirmation failed. Try signing in again.",
  config: "Server configuration error. Check Supabase environment variables.",
};

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = safeNextPath(searchParams.get("next"));
  const urlError = searchParams.get("error");
  const configured = useSupabaseConfigured();
  const { data: session, isPending } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isPending && session) {
      router.refresh();
      router.replace(next);
    }
  }, [session, isPending, router, next]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!configured) return;
    setSubmitting(true);
    try {
      const { error: err } = await getSupabaseBrowserClient().auth.signInWithPassword(
        { email: email.trim(), password },
      );
      if (err) {
        setError(err.message);
        return;
      }
      router.refresh();
      router.replace(next);
    } finally {
      setSubmitting(false);
    }
  }

  if (!configured) {
    return (
      <Alert>
        <AlertTitle>Supabase not configured</AlertTitle>
        <AlertDescription>
          Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to
          .env.local.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Log in</CardTitle>
        <CardDescription>Use your Supabase email and password.</CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit}>
        <CardContent className="space-y-4">
          {urlError && URL_ERROR_MESSAGES[urlError] ? (
            <Alert variant="destructive">
              <AlertTitle>Authentication</AlertTitle>
              <AlertDescription>{URL_ERROR_MESSAGES[urlError]}</AlertDescription>
            </Alert>
          ) : null}
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Sign-in failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4 border-t bg-muted/30 px-6 py-4">
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Signing in…" : "Continue"}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            No account?{" "}
            <Link href="/auth/signup" className="text-primary underline">
              Sign up
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
