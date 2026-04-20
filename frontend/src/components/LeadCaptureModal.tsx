"use client";

import { useCallback, useEffect, useId, useState } from "react";
import axios from "axios";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2, X } from "lucide-react";
import { getApiBaseUrl, publicResumeApi } from "@/lib/api";

export type LeadCaptureModalProps = {
  open: boolean;
  analysisId?: string | null;
  onClose: () => void;
  /** Called after lead is stored successfully; run PDF download here. */
  onSuccess: () => void | Promise<void>;
};

const emailOk = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim());

export default function LeadCaptureModal({
  open,
  analysisId,
  onClose,
  onSuccess,
}: LeadCaptureModalProps) {
  const titleId = useId();
  const [form, setForm] = useState({ full_name: "", email: "", phone: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setForm({ full_name: "", email: "", phone: "" });
      setError(null);
      setLoading(false);
    }
  }, [open]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setError(null);
  }, []);

  const validate = useCallback(() => {
    if (form.full_name.trim().length < 2) {
      return "Please enter your full name (at least 2 characters).";
    }
    if (!emailOk(form.email)) {
      return "Please enter a valid email address.";
    }
    const digits = form.phone.replace(/\D/g, "");
    if (digits.length < 8) {
      return "Please enter a phone number with at least 8 digits.";
    }
    if (form.phone.length > 32) {
      return "Phone number is too long.";
    }
    return null;
  }, [form]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const v = validate();
    if (v) {
      setError(v);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await publicResumeApi.post("/leads/", {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        analysis_id: analysisId || null,
      });
      await onSuccess();
      onClose();
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        if (err.code === "ERR_NETWORK" || err.message === "Network Error" || !err.response) {
          setError(
            `Cannot reach the API at ${getApiBaseUrl()}. Start the FastAPI backend, set NEXT_PUBLIC_API_URL in .env.local (e.g. http://localhost:8000), and ensure CORS allows this origin.`,
          );
          return;
        }
        const d = err.response?.data as { detail?: unknown } | undefined;
        if (typeof d?.detail === "string") {
          setError(d.detail);
        } else if (Array.isArray(d?.detail)) {
          setError(
            d.detail.map((x: { msg?: string }) => x.msg).filter(Boolean).join(" ") ||
              "Could not save your details.",
          );
        } else {
          setError("Could not save your details. Please try again.");
        }
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
          role="presentation"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(e) => {
            if (e.target === e.currentTarget && !loading) onClose();
          }}
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="relative w-full max-w-md rounded-micro-lg border border-gray-200 bg-white p-6 shadow-micro-lg sm:p-8"
            initial={{ scale: 0.94, opacity: 0, y: 12 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.96, opacity: 0, y: 8 }}
            transition={{ type: "spring", damping: 26, stiffness: 320 }}
          >
            <button
              type="button"
              onClick={() => !loading && onClose()}
              className="absolute right-4 top-4 rounded-micro p-1 text-microMuted transition hover:bg-microGray hover:text-microText"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>

            <h2
              id={titleId}
              className="pr-10 text-xl font-bold tracking-tight text-microText sm:text-2xl"
            >
              Download your AI report
            </h2>
            <p className="mt-2 text-sm text-microMuted">
              Share your details so the MicroDegree team can follow up. You can download your PDF
              right after submitting.
            </p>

            <form onSubmit={(e) => void handleSubmit(e)} className="mt-6 space-y-4">
              <div>
                <label htmlFor="lead-full_name" className="mb-1 block text-xs font-semibold text-microText">
                  Full name
                </label>
                <input
                  id="lead-full_name"
                  name="full_name"
                  type="text"
                  autoComplete="name"
                  value={form.full_name}
                  onChange={handleChange}
                  className="w-full rounded-micro border border-gray-200 px-3 py-2.5 text-sm text-microText shadow-sm outline-none transition focus:border-microRed focus:ring-2 focus:ring-microRed/20"
                  placeholder="Jane Doe"
                  disabled={loading}
                  required
                  minLength={2}
                />
              </div>
              <div>
                <label htmlFor="lead-email" className="mb-1 block text-xs font-semibold text-microText">
                  Email
                </label>
                <input
                  id="lead-email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={form.email}
                  onChange={handleChange}
                  className="w-full rounded-micro border border-gray-200 px-3 py-2.5 text-sm text-microText shadow-sm outline-none transition focus:border-microRed focus:ring-2 focus:ring-microRed/20"
                  placeholder="you@company.com"
                  disabled={loading}
                  required
                />
              </div>
              <div>
                <label htmlFor="lead-phone" className="mb-1 block text-xs font-semibold text-microText">
                  Phone
                </label>
                <input
                  id="lead-phone"
                  name="phone"
                  type="tel"
                  autoComplete="tel"
                  value={form.phone}
                  onChange={handleChange}
                  className="w-full rounded-micro border border-gray-200 px-3 py-2.5 text-sm text-microText shadow-sm outline-none transition focus:border-microRed focus:ring-2 focus:ring-microRed/20"
                  placeholder="+1 555 123 4567"
                  disabled={loading}
                  required
                />
              </div>

              {error ? (
                <p className="rounded-micro border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
                  {error}
                </p>
              ) : null}

              <motion.button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-micro-lg bg-gradient-to-r from-microRed to-microRedLight py-3 text-sm font-semibold text-white shadow-micro transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                whileHover={loading ? {} : { scale: 1.01 }}
                whileTap={loading ? {} : { scale: 0.99 }}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                    Submitting…
                  </>
                ) : (
                  "Submit & download PDF"
                )}
              </motion.button>

              <button
                type="button"
                onClick={() => !loading && onClose()}
                className="w-full py-2 text-center text-sm font-medium text-microMuted hover:text-microText"
                disabled={loading}
              >
                Cancel
              </button>
            </form>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
