"use client";

import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

export function LoadingAnimation({
  label = "Analyzing your resume…",
  /** Extra line under the label; pass null to hide. */
  secondary = "ATS scoring, skills mapping, and tailored suggestions",
}: {
  label?: string;
  secondary?: string | null;
}) {
  return (
    <motion.div
      className="flex flex-col items-center justify-center gap-6 py-16"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.35 }}
    >
      <motion.div
        className="relative flex h-20 w-20 items-center justify-center rounded-micro-lg bg-gradient-to-br from-microRed to-microRedLight shadow-micro-lg"
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
      >
        <motion.div
          className="absolute inset-2 rounded-micro border-2 border-white/30"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
        />
        <Loader2 className="relative z-10 h-9 w-9 text-white animate-spin" aria-hidden />
      </motion.div>
      <div className="text-center">
        <p className="text-sm font-semibold text-microText">{label}</p>
        {secondary != null && secondary !== "" ? (
          <p className="mt-2 max-w-md text-xs leading-relaxed text-microMuted">{secondary}</p>
        ) : null}
      </div>
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="h-2 w-2 rounded-full bg-microRed"
            animate={{ opacity: [0.3, 1, 0.3], y: [0, -6, 0] }}
            transition={{
              repeat: Infinity,
              duration: 0.9,
              delay: i * 0.15,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
    </motion.div>
  );
}
