"use client";

import { useEffect, useState } from "react";
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
import { useAuth } from "@/hooks/useAuth";
import { useProfile } from "@/hooks/use-profile";

export function ProfileForm() {
  const { user } = useAuth();
  const { data, isLoading, isError, error, updateProfile, updateState } =
    useProfile();
  const [displayName, setDisplayName] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [timezone, setTimezone] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!data) return;
    setDisplayName(data.display_name ?? "");
    setAvatarUrl(data.avatar_url ?? "");
    setTimezone(data.timezone ?? "");
  }, [data]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaved(false);
    await updateProfile({
      display_name: displayName.trim() || null,
      avatar_url: avatarUrl.trim() || null,
      timezone: timezone.trim() || null,
    });
    setSaved(true);
  }

  if (!user) {
    return null;
  }

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Profile</CardTitle>
        <CardDescription>
          Updates <code className="text-xs">public.users</code> with RLS (your
          row only). Email comes from Supabase Auth; change it in the Supabase
          dashboard or via a future account flow.
        </CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit}>
        <CardContent className="space-y-4">
          {isError ? (
            <Alert variant="destructive">
              <AlertTitle>Could not load profile</AlertTitle>
              <AlertDescription>
                {error instanceof Error ? error.message : "Unknown error"}
              </AlertDescription>
            </Alert>
          ) : null}
          {saved ? (
            <Alert>
              <AlertTitle>Saved</AlertTitle>
              <AlertDescription>Your profile was updated.</AlertDescription>
            </Alert>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="email">Email (read-only)</Label>
            <Input
              id="email"
              value={data?.email ?? user.email ?? ""}
              disabled
              readOnly
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="display_name">Display name</Label>
            <Input
              id="display_name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="How we greet you in the app"
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="avatar_url">Avatar URL</Label>
            <Input
              id="avatar_url"
              type="url"
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              placeholder="https://…"
              disabled={isLoading}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Input
              id="timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="e.g. America/New_York"
              disabled={isLoading}
            />
          </div>
          <Button type="submit" disabled={isLoading || updateState.isPending}>
            {updateState.isPending ? "Saving…" : "Save changes"}
          </Button>
          {updateState.isError ? (
            <p className="text-sm text-destructive">
              {updateState.error instanceof Error
                ? updateState.error.message
                : "Save failed"}
            </p>
          ) : null}
        </CardContent>
      </form>
    </Card>
  );
}
