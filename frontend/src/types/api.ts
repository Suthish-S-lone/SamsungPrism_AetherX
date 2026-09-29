/**
 * TypeScript interfaces matching SmartGuide FastAPI backend response models.
 */

export interface Step {
  text: string;
}

export interface Action {
  action_name: string;
  description: string;
  category: 'auto' | 'manual' | 'critical';
  steps: Step[];
  target_screen: string;
  deeplink: string | null;
}

export interface Context {
  goal: string;
  title: string;
  score: number;
  actions: Action[];
}

export interface QueryUnderstandingResult {
  original_query: string;
  normalized_query: string;
  domain: string | null;
  canonical_symptom: string | null;
  target_problem_id: string | null;
  extracted_signals: string[];
  confidence: number;
  reasoning_tags: string[];
  rewrite_method: string;
  fallback_used: boolean;
  is_out_of_scope: boolean;
}

export interface CandidateDebugInfo {
  problem_id: string;
  problem: string;
  domain: string;
  fused_score: number;
  bm25_rank: number | null;
  semantic_rank: number | null;
}

export interface RetrievalDebugInfo {
  queries_executed: string[];
  similarity_threshold: number;
  total_candidates_found: number;
  top_candidates: CandidateDebugInfo[];
  decision: string;
  confidence_level: string;
}

export interface LatencyBreakdown {
  query_understanding_ms: number;
  retrieval_ms: number;
  response_synthesis_ms: number;
  total_pipeline_ms: number;
}

export interface DiagnosticDebugMetadata {
  query_understanding: QueryUnderstandingResult;
  retrieval: RetrievalDebugInfo;
  latency: LatencyBreakdown;
}

export interface StructuredTroubleshootResponse {
  contexts: Context[];
  fallback: string | null;
  debug_info?: DiagnosticDebugMetadata | null;
}

export interface HealthResponse {
  status: string;
  data: string;
  schema: string;
  retrieval: string;
  cache: string;
  llm: string;
}
