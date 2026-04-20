"use client";

import { useCallback, useId, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Download, Loader2, Sparkles, Upload } from "lucide-react";
import { LoadingAnimation } from "@/components/resume/LoadingAnimation";
import { getApiBaseUrl } from "@/lib/api";
import type { PublicAnalyzeResponse } from "@/lib/resume-intelligence-types";

type Props = {
  file: File | null;
  onFileChange: (file: File | null) => void;
  onSuccess: (data: PublicAnalyzeResponse) => void;
  onClear?: () => void;
  /** Open lead capture before generating the PDF blob. */
  onRequestPdfDownload: () => void;
  pdfLoading?: boolean;
};

export function ResumeUpload({
  file,
  onFileChange,
  onSuccess,
  onClear,
  onRequestPdfDownload,
  pdfLoading = false,
}: Props) {
  const inputId = useId();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pickFile = useCallback(
    (f: File | undefined) => {
      if (!f) return;
      if (f.name.toLowerCase().endsWith(".pdf") || f.name.toLowerCase().endsWith(".docx")) {
        onFileChange(f);
        setError(null);
        onClear?.();
      } else {
        setError("Please upload a PDF or DOCX file.");
      }
    },
    [onClear, onFileChange],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (loading) return;
      setDrag(false);
      pickFile(e.dataTransfer.files[0]);
    },
    [loading, pickFile],
  );

  const analyze = async () => {
    if (loading) return;
    if (!file) {
      setError("Select a resume file to continue.");
      return;
    }
    const API_URL = getApiBaseUrl();
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const response = await fetch(`${API_URL}/public/analyze-resume?format=json`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let detail: string | undefined;
        try {
          const errBody = (await response.json()) as { detail?: unknown };
          if (typeof errBody.detail === "string") detail = errBody.detail;
        } catch {
          /* body not JSON */
        }
        setError(detail ?? `Request failed (${response.status}).`);
        return;
      }

      const data = (await response.json()) as PublicAnalyzeResponse;
      onSuccess(data);
    } catch {
      setError("Something went wrong while analyzing resume.");
    } finally {
      setLoading(false);
    }
  };

  const triggerFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-6">
      <motion.div
        id="md-resume-dropzone"
        aria-busy={loading}
        onDragOver={(e) => {
          if (loading) return;
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => {
          if (loading) return;
          setDrag(false);
        }}
        onDrop={onDrop}
        className={`rounded-xl border-2 border-dashed border-gray-300 bg-gray-50/80 p-10 text-center shadow-sm transition-colors duration-300 hover:border-red-400 ${
          drag && !loading ? "border-red-400 bg-red-50/30" : ""
        } ${loading ? "pointer-events-none" : ""}`}
      >
        {loading ? (
          <div role="status" aria-live="polite" aria-atomic="true">
            <LoadingAnimation
              label="Analyzing your resume…"
              secondary="This usually takes 30–40 seconds. Keep this tab open — we are scoring ATS fit, skills, and career paths."
            />
          </div>
        ) : (
          <>
            <div className="flex flex-col items-center text-center">
              <motion.div
                className="mb-3 flex justify-center text-red-500"
                animate={{ y: [0, -4, 0] }}
                transition={{ repeat: Infinity, duration: 2.5, ease: "easeInOut" }}
                aria-hidden
              >
                <Upload className="h-14 w-14 sm:h-16 sm:w-16" strokeWidth={1.5} />
              </motion.div>
              <h3 className="text-lg font-bold text-microText">Drop your resume here</h3>
              <p className="mt-1 text-sm text-microTextSecondary">PDF or DOCX · Private · No login</p>
              <div className="mt-6 flex flex-col items-center gap-2">
                <label
                  htmlFor={inputId}
                  className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#EF4444] to-[#F87171] px-6 py-3 text-center text-sm font-semibold text-white shadow-lg transition-all duration-300 hover:scale-[1.03] hover:shadow-xl"
                >
                  <Upload className="h-4 w-4" aria-hidden />
                  Upload Resume
                </label>
                <button
                  type="button"
                  onClick={triggerFileDialog}
                  className="px-4 py-2 text-sm text-gray-600 underline decoration-gray-400 underline-offset-2 transition-colors hover:text-gray-900 hover:decoration-gray-600"
                >
                  or browse files
                </button>
              </div>
              <input
                ref={fileInputRef}
                id={inputId}
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                className="sr-only"
                onChange={(e) => pickFile(e.target.files?.[0])}
              />
            </div>

            {file ? (
              <p className="mt-4 text-center text-sm font-medium text-microText">
                Selected: <span className="text-microBlue">{file.name}</span>
              </p>
            ) : null}

            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <motion.button
                type="button"
                disabled={!file || loading}
                onClick={() => void analyze()}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white shadow-md transition-all duration-300 hover:scale-[1.02] hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
                whileTap={file && !loading ? { scale: 0.98 } : {}}
              >
                <Sparkles className="h-4 w-4" aria-hidden />
                Analyze with AI
              </motion.button>
              <motion.button
                type="button"
                disabled={!file || pdfLoading}
                onClick={onRequestPdfDownload}
                className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm transition-all duration-300 hover:scale-[1.02] hover:bg-gray-100 sm:w-auto"
                whileTap={{ scale: 0.98 }}
              >
                {pdfLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Download PDF report
              </motion.button>
            </div>
          </>
        )}
      </motion.div>

      {error ? (
        <p className="rounded-micro border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
