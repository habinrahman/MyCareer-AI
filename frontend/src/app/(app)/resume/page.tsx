import { ResumeUploadPanel } from "@/components/resume/resume-upload-panel";

export default function ResumePage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Resume upload</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Files are sent to your API with your JWT. Analysis typically takes a
          few seconds.
        </p>
      </div>
      <ResumeUploadPanel />
    </div>
  );
}
