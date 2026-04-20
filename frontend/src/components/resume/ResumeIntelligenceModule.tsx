"use client";

import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import LeadCaptureModal from "@/components/LeadCaptureModal";
import { ResultsDashboard } from "@/components/resume/ResultsDashboard";
import { ResumeUpload } from "@/components/resume/ResumeUpload";
import { getApiBaseUrl } from "@/lib/api";
import type { PublicAnalyzeResponse } from "@/lib/resume-intelligence-types";

export function ResumeIntelligenceModule() {
  const [result, setResult] = useState<PublicAnalyzeResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [leadModalOpen, setLeadModalOpen] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [surfaceError, setSurfaceError] = useState<string | null>(null);

  const executePdfDownload = useCallback(async () => {
    if (!file) return;
    const API_URL = getApiBaseUrl();
    setPdfLoading(true);
    setSurfaceError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      console.log("Sending request…", { API_URL, format: "pdf", filename: file.name });
      const response = await fetch(`${API_URL}/public/analyze-resume?format=pdf`, {
        method: "POST",
        body: formData,
      });
      console.log("Response received:", response);

      if (!response.ok) {
        let msg = "Could not generate PDF. Try analyzing again.";
        try {
          const errBody = (await response.json()) as { detail?: unknown };
          if (typeof errBody.detail === "string") msg = errBody.detail;
        } catch {
          /* not JSON */
        }
        setSurfaceError(msg);
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${file.name.replace(/\.[^.]+$/, "")}-microdegree-review.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("API ERROR:", e);
      setSurfaceError("Something went wrong while generating the PDF.");
    } finally {
      setPdfLoading(false);
    }
  }, [file]);

  const openLeadGate = useCallback(() => {
    if (!file) {
      setSurfaceError("Upload a resume file first, then try downloading the PDF again.");
      document.getElementById("md-resume-dropzone")?.scrollIntoView({ behavior: "smooth" });
      return;
    }
    setSurfaceError(null);
    setLeadModalOpen(true);
  }, [file]);

  return (
    <div className="resume-intelligence-root flex flex-1 flex-col bg-microGray">
      <header className="relative z-0 overflow-hidden bg-gradient-to-br from-[#DC2626] via-[#EF4444] to-[#F87171] px-4 pb-24 pt-4 sm:px-6 sm:pb-28 sm:pt-6 lg:px-8">
        <div className="pointer-events-none absolute left-[-120px] top-[-120px] h-[400px] w-[400px] rounded-full bg-red-300/30 blur-[120px]" />
        <div className="pointer-events-none absolute bottom-[-100px] right-[-100px] h-[400px] w-[400px] rounded-full bg-pink-300/30 blur-[120px]" />
        <div className="relative z-10 mx-auto max-w-3xl py-8 text-center">
          <motion.div
            className="mb-4 inline-block rounded-full bg-white/20 px-4 py-1 text-xs font-medium text-white"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            POWERED BY MICRODEGREE AI
          </motion.div>
          <motion.h1
            className="text-4xl font-bold tracking-tight text-white md:text-5xl"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
          >
            AI Resume Intelligence
          </motion.h1>
          <motion.p
            className="mt-4 text-lg text-white/90"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.12 }}
          >
            Transform your resume into a clear career plan with AI-powered insights.
          </motion.p>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-6xl px-4 pb-20 sm:px-6 lg:px-8">
        <motion.div
          className="relative z-10 -mt-24 rounded-2xl bg-white p-10 shadow-[0_30px_80px_rgba(0,0,0,0.18)] transition-all duration-300 sm:p-12"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.15 }}
        >
          {surfaceError ? (
            <p
              className="mb-4 rounded-micro border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
              role="status"
            >
              {surfaceError}
            </p>
          ) : null}
          <ResumeUpload
            file={file}
            onFileChange={setFile}
            onSuccess={setResult}
            onClear={() => setResult(null)}
            onRequestPdfDownload={openLeadGate}
            pdfLoading={pdfLoading}
          />
        </motion.div>

        {result ? (
          <div className="mt-12">
            <motion.h2
              className="mb-8 text-center text-3xl font-bold text-microText sm:text-4xl"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              Your intelligence dashboard
            </motion.h2>
            <ResultsDashboard
              data={result}
              canDownloadPdf={!!file}
              onRequestPdfDownload={openLeadGate}
              pdfLoading={pdfLoading}
            />
          </div>
        ) : null}
      </main>

      <footer className="border-t border-gray-200 bg-white py-8 text-center text-xs text-microMuted">
        <p>
          Resume Intelligence by{" "}
          <span className="font-semibold text-microRed">MicroDegree</span> · Results are generated
          for guidance only.
        </p>
      </footer>

      <LeadCaptureModal
        open={leadModalOpen}
        analysisId={null}
        onClose={() => setLeadModalOpen(false)}
        onSuccess={() => executePdfDownload()}
      />
    </div>
  );
}
