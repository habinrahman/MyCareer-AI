/**
 * Build-time flags (NEXT_PUBLIC_*). V1 MVP: public resume review only; flip for V2+.
 */
export const featureFlags = {
  auth: process.env.NEXT_PUBLIC_ENABLE_AUTH === "true",
  chat: process.env.NEXT_PUBLIC_ENABLE_CHAT === "true",
  benchmarking: process.env.NEXT_PUBLIC_ENABLE_BENCHMARKING === "true",
  jobMatching: process.env.NEXT_PUBLIC_ENABLE_JOB_MATCHING === "true",
  recruiterMode: process.env.NEXT_PUBLIC_ENABLE_RECRUITER_MODE === "true",
  /** Authenticated workspace (dashboard, saved resume flow, reports list, etc.) */
  workspace:
    process.env.NEXT_PUBLIC_ENABLE_WORKSPACE !== "false",
  reports: process.env.NEXT_PUBLIC_ENABLE_REPORTS !== "false",
  publicResumeReview: process.env.NEXT_PUBLIC_PUBLIC_RESUME_REVIEW === "true",
} as const;
