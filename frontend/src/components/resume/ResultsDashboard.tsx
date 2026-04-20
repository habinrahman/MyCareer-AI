"use client";

import { motion } from "framer-motion";
import { Briefcase, Download, Lightbulb, Loader2, Target } from "lucide-react";
import { ATSGauge } from "@/components/resume/ATSGauge";
import { KeywordBarChart } from "@/components/resume/KeywordBarChart";
import { SkillsRadarChart } from "@/components/resume/SkillsRadarChart";
import { LearningPaths } from "@/components/resume/LearningPaths";
import RecommendedVideos from "@/components/RecommendedVideos";
import { StrengthsCard } from "@/components/resume/StrengthsCard";
import { WeaknessesCard } from "@/components/resume/WeaknessesCard";
import type { PublicAnalyzeResponse } from "@/lib/resume-intelligence-types";

function ResumeScoreBar({ score }: { score: number }) {
  const safe = Math.max(0, Math.min(100, Math.round(score)));
  return (
    <motion.div
      className="rounded-micro-lg border border-gray-100 bg-white p-6 shadow-micro"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wide text-microMuted">
            Resume score
          </h3>
          <p className="text-xs text-microMuted">Holistic quality estimate</p>
        </div>
        <span className="text-3xl font-bold tabular-nums text-microBlue">{safe}</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-gray-100">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-microBlue to-microRed"
          initial={{ width: 0 }}
          animate={{ width: `${safe}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
    </motion.div>
  );
}

type ResultsDashboardProps = {
  data: PublicAnalyzeResponse;
  canDownloadPdf?: boolean;
  onRequestPdfDownload?: () => void;
  pdfLoading?: boolean;
};

export function ResultsDashboard({
  data,
  canDownloadPdf = false,
  onRequestPdfDownload,
  pdfLoading = false,
}: ResultsDashboardProps) {
  const ats = data.analysis.ats_compatibility?.score ?? data.scores.ats_score;

  return (
    <motion.section
      className="space-y-10"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {onRequestPdfDownload ? (
        <motion.div
          className="rounded-micro-lg border border-microBlue/25 bg-gradient-to-r from-microBlue/[0.07] to-microRed/[0.06] p-6 shadow-micro sm:flex sm:items-center sm:justify-between sm:gap-6 sm:p-8"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="min-w-0">
            <h3 className="text-lg font-bold text-microText">Download PDF report</h3>
            <p className="mt-1 text-sm text-microTextSecondary">
              Get a shareable MicroDegree-branded PDF. We will ask for your contact details first so
              our team can follow up.
            </p>
          </div>
          <motion.button
            type="button"
            disabled={!canDownloadPdf || pdfLoading}
            onClick={onRequestPdfDownload}
            className="mt-4 inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-micro-lg bg-gradient-to-r from-microRed to-microRedLight px-6 py-3 text-sm font-semibold text-white shadow-micro transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50 sm:mt-0 sm:w-auto"
            whileHover={canDownloadPdf && !pdfLoading ? { scale: 1.02 } : {}}
            whileTap={canDownloadPdf && !pdfLoading ? { scale: 0.98 } : {}}
          >
            {pdfLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Download className="h-4 w-4" aria-hidden />
            )}
            {pdfLoading ? "Preparing…" : "Download PDF report"}
          </motion.button>
        </motion.div>
      ) : null}

      <motion.div
        className="rounded-micro-lg border border-gray-100 bg-white p-6 shadow-micro sm:p-8"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-2xl font-bold text-microText sm:text-3xl">Executive summary</h2>
        <p className="mt-3 text-sm leading-relaxed text-microTextSecondary sm:text-base">{data.summary}</p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ATSGauge score={ats} />
        <ResumeScoreBar score={data.scores.resume_score} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SkillsRadarChart data={data} />
        <KeywordBarChart data={data} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <StrengthsCard items={data.analysis.strengths} />
        <WeaknessesCard items={data.analysis.weaknesses} />
      </div>

      {(data.analysis.skill_gap_analysis?.gaps?.length ?? 0) > 0 ? (
        <motion.div
          className="rounded-micro-lg border border-microBlue/20 bg-gradient-to-br from-microBlue/[0.06] to-white p-6 shadow-micro sm:p-8"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="mb-4 flex items-center gap-2">
            <Target className="h-5 w-5 text-microBlue" />
            <h3 className="text-lg font-bold text-microText">Skill gap analysis</h3>
          </div>
          {data.analysis.skill_gap_analysis.industry_context ? (
            <p className="mb-4 text-sm text-microTextSecondary">
              {data.analysis.skill_gap_analysis.industry_context}
            </p>
          ) : null}
          <ul className="space-y-3">
            {data.analysis.skill_gap_analysis.gaps.map((g, i) => (
              <li
                key={`${g.skill}-${i}`}
                className="rounded-micro border border-gray-100 bg-white/80 px-4 py-3"
              >
                <span className="font-semibold text-microText">{g.skill}</span>
                <span className="ml-2 text-xs uppercase text-microMuted">{g.importance}</span>
                {g.gap_description ? (
                  <p className="mt-1 text-sm text-microTextSecondary">{g.gap_description}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </motion.div>
      ) : null}

      <motion.div
        className="rounded-micro-lg border border-gray-100 bg-white p-6 shadow-micro sm:p-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="mb-4 flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-microRed" />
          <h3 className="text-lg font-bold text-microText">Recommendations</h3>
        </div>
        <div className="grid gap-8 md:grid-cols-2">
          <div>
            <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-microMuted">
              Actionable improvements
            </h4>
            {(data.analysis.improvement_suggestions ?? []).length ? (
              <ul className="space-y-2 text-sm text-microTextSecondary">
                {(data.analysis.improvement_suggestions ?? []).map((s, i) => (
                  <li key={`imp-${i}`} className="flex gap-2">
                    <span className="text-microRed">→</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-microMuted">No suggestions returned for this run.</p>
            )}
          </div>
          <div>
            <h4 className="mb-2 flex items-center gap-1 text-xs font-bold uppercase tracking-wide text-microMuted">
              <Briefcase className="h-3.5 w-3.5" />
              Suggested roles
            </h4>
            {(data.analysis.recommended_roles ?? []).length ? (
              <ul className="space-y-2 text-sm text-microTextSecondary">
                {(data.analysis.recommended_roles ?? []).map((r, i) => (
                  <li key={`role-${i}`} className="rounded-micro bg-microGrayMuted px-3 py-2 font-medium">
                    {r}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-microMuted">No role suggestions in this response.</p>
            )}
          </div>
        </div>
        <LearningPaths paths={data.analysis.course_recommendations ?? []} />
        <RecommendedVideos roles={data.analysis.recommended_roles ?? []} />
      </motion.div>
    </motion.section>
  );
}
