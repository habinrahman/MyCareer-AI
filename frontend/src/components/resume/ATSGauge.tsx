"use client";

import { motion } from "framer-motion";
import {
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
} from "recharts";

function fillForScore(score: number): string {
  if (score >= 85) return "#16a34a";
  if (score >= 75) return "#2563EB";
  if (score >= 60) return "#d97706";
  return "#ea580c";
}

function labelForScore(score: number): string {
  if (score >= 85) return "Excellent";
  if (score >= 75) return "Strong";
  if (score >= 60) return "Good";
  return "Needs improvement";
}

export function ATSGauge({ score }: { score: number }) {
  const safe = Math.max(0, Math.min(100, Math.round(score)));
  const fill = fillForScore(safe);
  const data = [{ name: "ATS", value: safe, fill }];

  return (
    <motion.div
      className="rounded-micro-lg border border-gray-100 bg-white p-6 shadow-micro"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >
      <h3 className="text-center text-sm font-bold uppercase tracking-wide text-microMuted">
        ATS compatibility
      </h3>
      <div className="relative mx-auto h-[200px] w-full min-h-[200px] max-w-[220px]">
        <ResponsiveContainer width="100%" height={200}>
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="72%"
            outerRadius="100%"
            barSize={16}
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              dataKey="value"
              cornerRadius={12}
              background={{ fill: "#E5E7EB" }}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pt-2">
          <span className="text-4xl font-bold tabular-nums text-microText">{safe}</span>
          <span className="text-xs font-medium text-microMuted">out of 100</span>
        </div>
      </div>
      <p
        className="mt-2 text-center text-sm font-semibold"
        style={{ color: fill }}
      >
        {labelForScore(safe)}
      </p>
      {safe < 85 ? (
        <p className="mt-2 text-center text-xs text-microMuted">
          Missing quantified impact — add metrics to reach 85+.
        </p>
      ) : null}
      <p className="mt-3 text-center text-[11px] font-medium uppercase tracking-wide text-microLight">
        Confidence: High · Based on 120+ ATS signals
      </p>
    </motion.div>
  );
}
