import { ProfileForm } from "@/components/settings/profile-form";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Account &amp; profile</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Manage your app profile. Session cookies are refreshed by middleware on
          each request for secure access to the workspace.
        </p>
      </div>
      <ProfileForm />
    </div>
  );
}
