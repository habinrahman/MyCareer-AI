"use client";

import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

export function StrengthsCard({ items }: { items: string[] }) {
  if (!items?.length) return null;

  return (
    <motion.div
      className="rounded-micro-lg border border-emerald-200/80 bg-gradient-to-br from-emerald-50/90 to-white p-6 shadow-micro"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.06 }}
    >
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-micro bg-emerald-100">
          <CheckCircle2 className="h-5 w-5 text-emerald-700" aria-hidden />
        </div>
        <div>
          <h3 className="text-lg font-bold text-microText">Strengths</h3>
          <p className="text-xs text-microMuted">What already works in your favor</p>
        </div>
      </div>
      <ul className="space-y-3">
        {items.map((item, i) => (
          <motion.li
            key={`${i}-s`}
            className="flex gap-3 text-sm leading-relaxed text-microTextSecondary"
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * i }}
          >
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
            <span>{item}</span>
          </motion.li>
        ))}
      </ul>
    </motion.div>
  );
}
