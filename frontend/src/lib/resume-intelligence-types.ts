/** Response shape from POST /public/analyze-resume (JSON). */

export type PublicAnalyzeResponse = {
  summary: string;
  parsed_char_count: number;
  scores: {
    resume_score: number;
    ats_score: number;
    model: string;
    prompt_version: string;
  };
  analysis: {
    strengths: string[];
    weaknesses: string[];
    improvement_suggestions: string[];
    recommended_roles: string[];
    skills_assessment?: {
      technical_skills: string[];
      soft_skills: string[];
      proficiency_notes?: string;
    };
    skill_gap_analysis: {
      gaps: Array<{ skill: string; gap_description: string; importance: string }>;
      industry_context: string;
    };
    ats_compatibility: {
      score: number;
      keywords_match: string[];
      formatting_notes: string;
      suggestions: string[];
    };
    structured_resume?: {
      basics?: {
        name?: string | null;
        email?: string | null;
        phone?: string | null;
        linkedin?: string | null;
        github?: string | null;
      } | null;
      skills?: string[];
    };
    course_recommendations: Array<{
      title: string;
      provider?: string | null;
      rationale: string;
    }>;
  };
};
