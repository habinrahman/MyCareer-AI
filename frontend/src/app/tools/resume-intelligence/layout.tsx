import type { Metadata } from "next";
import Header from "@/components/Header";
import "@/styles/microdegree-resume.css";

export const metadata: Metadata = {
  title: "AI Resume Intelligence | MicroDegree",
  description:
    "Upload your resume for ATS scoring, skill insights, and career recommendations — powered by MicroDegree AI.",
};

export default function ResumeIntelligenceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col gap-6 bg-microGray">
      <Header />
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
