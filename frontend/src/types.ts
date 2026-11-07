export type Role = "participant" | "organizer";
export type Difficulty = "easy" | "medium" | "hard";
export type Language = "python" | "cpp" | "java" | "javascript";
export type Verdict = "OK" | "WA" | "TLE" | "RE" | "CE";
export type Phase = "draft" | "upcoming" | "running" | "finished";

export interface User {
  id: number;
  username: string;
  email: string;
  role: Role;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Problem {
  id: number;
  title: string;
  short_description: string;
  difficulty: Difficulty;
  accepted_count: number;
  solved_by_me: boolean;
}

export interface Example {
  input: string;
  output: string;
}

export interface ProblemDetail extends Problem {
  statement: string;
  input_format: string;
  output_format: string;
  constraints: string;
  time_limit_ms: number;
  memory_limit_mb: number;
  examples: Example[];
}

export interface JudgeResult {
  verdict: Verdict;
  message: string | null;
  runtime_ms: number | null;
  tests_passed: number;
  tests_total: number;
  judge_mode: "demo" | "judge0";
  judge_label: string;
  samples_only: boolean;
  failed_input: string | null;
  failed_expected: string | null;
  failed_actual: string | null;
}

export interface Submission extends JudgeResult {
  id: number;
  problem_id: number;
  problem_title: string | null;
  contest_id: number | null;
  language: Language;
  source_code: string | null;
  created_at: string;
}

export interface ContestProblem {
  problem_id: number;
  order_index: number;
  code: string;
  title: string;
  difficulty: Difficulty;
  solved_by_me: boolean;
}

export interface Contest {
  id: number;
  title: string;
  description: string;
  problem_count: number;
  start_time: string;
  duration_minutes: number;
  phase: Phase;
  is_registered: boolean;
  is_owner: boolean;
  organizer_name: string;
  problems: ContestProblem[];
}

export interface Standing {
  place: number;
  user_id: number;
  username: string;
  solved: number;
  time_seconds: number;
}

export interface Dashboard {
  username: string;
  solved_count: number;
  submission_count: number;
  contests: Contest[];
  recent_submissions: Submission[];
}

export interface SystemInfo {
  judge_mode: "demo" | "judge0";
  judge_label: string;
  languages: Language[];
}

export interface ContestPayload {
  title: string;
  description: string;
  start_time: string;
  duration_minutes: number;
  problem_ids: number[];
}
