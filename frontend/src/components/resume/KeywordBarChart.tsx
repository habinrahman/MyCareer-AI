"use client";

import { motion } from "framer-motion";
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PublicAnalyzeResponse } from "@/lib/resume-intelligence-types";

const BAR_COLORS = ["#2563EB", "#3B82F6", "#EF4444", "#DC2626", "#7c3aed", "#0d9488"];

export function KeywordBarChart({ data }: { data: PublicAnalyzeResponse }) {
  const keywords = data.analysis.ats_compatibility?.keywords_match ?? [];
  const ats = data.analysis.ats_compatibility?.score ?? data.scores.ats_score;

  const chartData =
    keywords.length > 0
      ? keywords.slice(0, 10).map((k, i) => ({
          name: k.length > 22 ? `${k.slice(0, 20)}…` : k,
          full: k,
          weight: Math.max(35, Math.min(100, ats - i * 4 + (i % 3) * 5)),
        }))
      : [
          { name: "Add keywords", full: "Upload a JD-aligned resume for keyword signals", weight: 40 },
        ];

  return (
    <motion.div
      className="rounded-micro-lg border border-gray-100 bg-white p-4 shadow-micro sm:p-6"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.12 }}
    >
      <h3 className="mb-1 text-sm font-bold uppercase tracking-wide text-microMuted">
        ATS keyword signals
      </h3>
      <p className="mb-4 text-xs text-microMuted">
        Relative emphasis from detected or suggested ATS-relevant terms.
      </p>
      <div className="h-[280px] w-full min-h-[280px]">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
          >
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#6B7280" }} />
            <YAxis
              type="category"
              dataKey="name"
              width={120}
              tick={{ fontSize: 10, fill: "#374151" }}
            />
            <Tooltip
              formatter={(value) => [
                `${Math.round(Number(value ?? 0))}`,
                "Signal",
              ]}
              labelFormatter={(_, payload) =>
                String(
                  (payload?.[0]?.payload as { full?: string } | undefined)?.full ??
                    "",
                )
              }
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #e5e7eb",
                fontSize: 12,
              }}
            />
            <Bar dataKey="weight" radius={[0, 8, 8, 0]} maxBarSize={22}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
