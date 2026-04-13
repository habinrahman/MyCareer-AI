export type MentorStructured = {
  role_recommendations: string[];
  skill_gap_notes: string[];
  interview_prep: string[];
  learning_roadmap: string[];
};

export type AnalysisPayload = {
  structured_resume?: Record<string, unknown>;
  resume_score?: number;
  professional_summary?: string;
  strengths?: string[];
  weaknesses?: string[];
  ats_compatibility?: {
    score: number;
    keywords_match?: string[];
    formatting_notes?: string;
    suggestions?: string[];
  };
  skills_assessment?: {
    technical_skills?: string[];
    soft_skills?: string[];
    proficiency_notes?: string;
  };
  skill_gap_analysis?: {
    gaps?: { skill: string; gap_description?: string; importance?: string }[];
    industry_context?: string;
  };
  recommended_roles?: string[];
  career_outlook?: string;
  improvement_suggestions?: string[];
  course_recommendations?: {
    title: string;
    provider?: string | null;
    rationale?: string;
  }[];
};

export type AnalyzeResumeResponse = {
  resume_id: string;
  analysis_id: string;
  analysis_version: number;
  summary: string;
  parsed_char_count: number;
  analysis: AnalysisPayload;
};

export type ChatHistoryMessage = {
  id: string;
  role: string;
  content: string;
  created_at: string;
};

export type ChatHistoryResponse = {
  session_id: string;
  messages: ChatHistoryMessage[];
};
