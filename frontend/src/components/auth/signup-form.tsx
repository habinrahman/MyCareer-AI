"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
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
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

export function SignupForm() {
  const router = useRouter();
  const configured = useSupabaseConfigured();
  const { data: session, isPending } = useSession();
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isPending && session) {
      router.refresh();
      router.replace("/dashboard");
    }
  }, [session, isPending, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    if (!configured) return;
    setSubmitting(true);
    try {
      const origin =
        typeof window !== "undefined" ? window.location.origin : "";
      const { data, error: err } = await getSupabaseBrowserClient().auth.signUp({
        email: email.trim(),
        password,
        options: {
          emailRedirectTo: origin
            ? `${origin}/auth/callback?next=/dashboard`
            : undefined,
          data: {
            display_name: displayName.trim() || undefined,
          },
        },
      });
      if (err) {
        setError(err.message);
        return;
      }
      if (data.session) {
        router.refresh();
        router.replace("/dashboard");
        return;
      }
      setInfo(
        "Check your email to confirm your account, then return here to log in.",
      );
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
        <CardTitle>Create account</CardTitle>
        <CardDescription>
          We use Supabase Auth. Email confirmation may be required depending on
          your project settings.
        </CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit}>
        <CardContent className="space-y-4">
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Sign-up failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          {info ? (
            <Alert>
              <AlertTitle>Almost there</AlertTitle>
              <AlertDescription>{info}</AlertDescription>
            </Alert>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="su-display">Display name (optional)</Label>
            <Input
              id="su-display"
              type="text"
              autoComplete="name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Shown in MyCareer AI"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="su-email">Email</Label>
            <Input
              id="su-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="su-password">Password</Label>
            <Input
              id="su-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4 border-t bg-muted/30 px-6 py-4">
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Creating…" : "Sign up"}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/auth/login" className="text-primary underline">
              Log in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
