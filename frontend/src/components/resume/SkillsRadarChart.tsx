"use client";

import { motion } from "framer-motion";
import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import type { PublicAnalyzeResponse } from "@/lib/resume-intelligence-types";

function buildRadarRows(data: PublicAnalyzeResponse) {
  const tech = data.analysis.skills_assessment?.technical_skills?.length ?? 0;
  const soft = data.analysis.skills_assessment?.soft_skills?.length ?? 0;
  const kw = data.analysis.ats_compatibility?.keywords_match?.length ?? 0;
  const resume = data.scores.resume_score;
  const ats = data.analysis.ats_compatibility?.score ?? data.scores.ats_score;

  return [
    {
      skill: "Technical",
      value: Math.min(100, tech * 7 + 28),
    },
    {
      skill: "Soft skills",
      value: Math.min(100, soft * 9 + 22),
    },
    {
      skill: "ATS match",
      value: ats,
    },
    {
      skill: "Overall polish",
      value: resume,
    },
    {
      skill: "Keywords",
      value: Math.min(100, kw * 11 + 30),
    },
  ];
}

export function SkillsRadarChart({ data }: { data: PublicAnalyzeResponse }) {
  const rows = buildRadarRows(data);

  return (
    <motion.div
      className="rounded-micro-lg border border-gray-100 bg-white p-4 shadow-micro sm:p-6"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: 0.08 }}
    >
      <h3 className="mb-1 text-sm font-bold uppercase tracking-wide text-microMuted">
        Skills profile
      </h3>
      <p className="mb-4 text-xs text-microMuted">
        Derived from your resume content and ATS signals (illustrative axes).
      </p>
      <div className="h-[280px] w-full min-h-[280px]">
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={rows}>
            <PolarGrid stroke="#E5E7EB" />
            <PolarAngleAxis
              dataKey="skill"
              tick={{ fill: "#6B7280", fontSize: 11 }}
            />
            <Radar
              name="Score"
              dataKey="value"
              stroke="#EF4444"
              fill="#EF4444"
              fillOpacity={0.35}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
