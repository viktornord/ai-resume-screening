export type YearsMatch = "clear" | "not_enough" | "ambiguous" | "n/a";

export interface MatchingSkill {
  name: string;
  years_match: YearsMatch;
  description: string;
}

export interface NotMentionedSkill {
  name: string;
  description: string;
}

export interface Candidate {
  candidate_name: string;
  match_score: number;
  matching_skills: MatchingSkill[];
  not_mentioned_skills: NotMentionedSkill[];
  recommendation: string;
  source_filename: string;
  reasoning: string;
  ambiguities: string[];
}

export interface ScreenResponse {
  job_title_hint: string | null;
  requirements_reasoning: string;
  requirements_ambiguities: string[];
  candidates: Candidate[];
  screened_at: string;
  processing_ms: number;
}

export interface HealthResponse {
  status: string;
  llm_reachable: boolean;
  model_ready: boolean;
}
