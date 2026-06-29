// allow: SIZE_OK — shared contract barrel keeps exported provider records discoverable.
export interface Tenant {
  id: string;
  name: string;
  domain: string;
  environment: "production" | "test";
}

export interface DealRecord {
  id: string;
  tenant_id: string;
  account_name: string;
  name: string;
  owner_name: string;
  amount_usd: number;
  stage: string;
  status: "healthy" | "stalling";
  close_date: string;
}

export interface AccountRecord {
  id: string;
  tenant_id: string;
  record_type: "account";
  name: string;
  domain: string;
  owner_user_id: string;
  segment: string;
  health: "healthy" | "at_risk";
  renewal_date: string | null;
}

export interface RoleRecord {
  id: string;
  tenant_id: string;
  record_type: "role";
  name: string;
  permissions: string[];
}

export interface UserRecord {
  id: string;
  tenant_id: string;
  record_type: "user";
  name: string;
  email: string;
  role_id: string;
  role_name: string;
  manager_id: string | null;
  status: "active" | "disabled";
}

export interface AdminSettingRecord {
  id: string;
  tenant_id: string;
  record_type: "admin_setting";
  key: string;
  value: string;
  updated_at: string;
}

export interface ContactRecord {
  id: string;
  tenant_id: string;
  deal_id: string;
  name: string;
  title: string;
  email: string;
}

export interface ObjectionRecord {
  type: string;
  verbatim_quote: string;
  contact_id: string;
  severity: "low" | "medium" | "high";
}

export interface CommitmentRecord {
  type: string;
  made_by_contact_id: string;
  due_date?: string;
  verbatim: string;
}

export interface SentimentShift {
  contact_id: string;
  from: "positive" | "neutral" | "negative";
  to: "positive" | "neutral" | "negative";
  timestamp_in_call: number;
  trigger_quote: string;
}

export interface CompetitiveMention {
  competitor_name: string;
  context: string;
  sentiment: "positive" | "neutral" | "negative";
}

export interface ChampionBehaviorSignal {
  contact_id: string | null;
  signal_type: "active_advocacy" | "passive" | "silence" | "opposition";
  evidence_quote: string;
}

export interface DealMemory {
  deal_id: string;
  tenant_id: string;
  stage: string;
  champion_id: string | null;
  economic_buyer_id: string | null;
  champion_confidence: number;
  budget_confirmed: boolean;
  technical_validated: boolean;
  active_objections: string[];
  next_step_agreed: string | null;
  last_call_id: string;
  valid_from: string;
  valid_to: string | null;
}

export interface ContactMemory {
  contact_id: string;
  deal_id: string;
  tenant_id: string;
  role: "champion" | "economic_buyer" | "technical_buyer" | "blocker" | "unknown";
  engagement_level: "high" | "medium" | "low" | "silent";
  last_seen_on_call: string;
  last_seen_timestamp: string;
  sentiment_trend: "positive" | "neutral" | "negative" | "declining";
  key_concerns: string[];
  valid_from: string;
  valid_to: string | null;
}

export interface CallEvent {
  call_id: string;
  deal_id: string;
  tenant_id: string;
  timestamp: string;
  duration_seconds: number;
  participants: string[];
  objections_raised: ObjectionRecord[];
  commitments_made: CommitmentRecord[];
  sentiment_shifts: SentimentShift[];
  competitive_mentions: CompetitiveMention[];
  champion_behavior: ChampionBehaviorSignal;
  summary: string;
}

export interface CallLibraryRecord {
  id: string;
  tenant_id: string;
  record_type: "call_library_entry";
  call_id: string;
  deal_id: string;
  account_id: string;
  title: string;
  started_at: string;
  duration_seconds: number;
  primary_rep_id: string;
  outcome: string;
  recording_url: string | null;
  transcript_id: string;
}

export interface CoachingScorecard {
  id: string;
  tenant_id: string;
  record_type: "coaching_scorecard";
  rep_id: string;
  call_id: string;
  deal_id: string;
  reviewer_user_id: string;
  overall_score: number;
  strengths: string[];
  improvement_areas: string[];
  reviewed_at: string;
}

export interface ForecastSubmission {
  id: string;
  tenant_id: string;
  record_type: "forecast_submission";
  period: string;
  submitted_by_user_id: string;
  forecast_category: string;
  commit_amount_usd: number;
  best_case_amount_usd: number;
  pipeline_amount_usd: number;
  submitted_at: string;
}

export interface EngagementTask {
  id: string;
  tenant_id: string;
  record_type: "engagement_task";
  deal_id: string;
  account_id: string;
  owner_user_id: string;
  title: string;
  due_date: string;
  priority: "low" | "medium" | "high";
  status: "open" | "done" | "blocked";
  source_call_id: string | null;
}

export interface AssistantAnswer {
  id: string;
  tenant_id: string;
  record_type: "assistant_answer";
  question: string;
  answer: string;
  citation_ids: string[];
  created_at: string;
  created_by_user_id: string;
}

export interface AuditEvent {
  id: string;
  tenant_id: string;
  record_type: "audit_event";
  actor_user_id: string;
  action: string;
  target_type: string;
  target_id: string;
  occurred_at: string;
}

export interface ExportJob {
  id: string;
  tenant_id: string;
  record_type: "export_job";
  requested_by_user_id: string;
  export_type: string;
  status: "pending" | "ready" | "failed";
  created_at: string;
  completed_at: string | null;
  download_url: string | null;
}

export type ProductionProviderRecord =
  | AccountRecord
  | RoleRecord
  | UserRecord
  | AdminSettingRecord
  | CallLibraryRecord
  | CoachingScorecard
  | ForecastSubmission
  | EngagementTask
  | AssistantAnswer
  | AuditEvent
  | ExportJob;

export type CausalLinkType =
  | "champion_silence_triggered_budget_objection"
  | "competitor_mention_triggered_pricing_concern"
  | "economic_buyer_absence_triggered_stall"
  | "technical_objection_resolved_by_validation"
  | "champion_change_triggered_restart"
  | "commitment_broken_triggered_trust_loss"
  | "stage_regression_triggered_by"
  | string;

export interface CausalLink {
  tenant_id: string;
  deal_id: string;
  from_node_id: string;
  to_node_id: string;
  link_type: CausalLinkType;
  confidence: number;
  evidence_call_id: string;
  created_at: string;
}

export interface ObjectionHandler {
  objection_type: string;
  guidance: string;
  evidence_required: string[];
}

export interface Playbook {
  id: string;
  tenant_id: string;
  stage: string;
  title: string;
  content: string;
  objection_handlers: ObjectionHandler[];
  version: number;
  active: boolean;
}

export interface Battlecard {
  id: string;
  tenant_id: string;
  competitor_name: string;
  our_strengths: string[];
  their_weaknesses: string[];
  traps_to_avoid: string[];
  win_themes: string[];
  version: number;
  active: boolean;
}

export interface ICPDefinition {
  id: string;
  tenant_id: string;
  segment: string;
  firmographic_criteria: Record<string, string | number | boolean | readonly string[]>;
  behavioral_signals: string[];
  disqualifiers: string[];
  version: number;
  active: boolean;
}

export interface SourceFact {
  id: string;
  tenant_id: string;
  record_type: "source_fact";
  source?: string;
  content?: string;
  deal_id?: string;
  source_record_id?: string;
  stage?: string;
}

export interface IntegrationFact {
  id: string;
  tenant_id: string;
  record_type: "integration_fact";
  source?: string;
  content?: string;
  deal_id?: string;
  source_record_id?: string;
  stage?: string;
  amount?: number;
}

export type KnowledgeRecord = Playbook | Battlecard | ICPDefinition;
export type KnowledgeNodeRecord = KnowledgeRecord | SourceFact | IntegrationFact;

export interface MemoryNode<T = DealMemory | ContactMemory | CallEvent> {
  id: string;
  tenant_id: string;
  kind: "DealMemory" | "ContactMemory" | "CallEvent";
  record: T;
}

export interface KnowledgeNode<T = KnowledgeNodeRecord> {
  id: string;
  tenant_id: string;
  kind: "Playbook" | "Battlecard" | "ICPDefinition" | "SourceFact" | "IntegrationFact";
  record: T;
}

export interface DealContext {
  tenant: Tenant;
  deal: DealRecord;
  contacts: ContactRecord[];
  deal_memory: DealMemory;
  contact_memories: ContactMemory[];
  call_events: CallEvent[];
  causal_links: CausalLink[];
  knowledge_nodes: KnowledgeNode[];
}

export interface CausalChain {
  deal_id: string;
  tenant_id: string;
  links: CausalLink[];
}

export interface CausalDiagnosis {
  readonly description: string;
  readonly causal_chain: readonly string[];
  readonly evidence_node_ids: readonly string[];
}

export interface RiskFlag {
  readonly flag: string;
  readonly severity: string;
  readonly evidence_node_id: string;
}

export interface NextBestAction {
  readonly action: string;
  readonly rationale: string;
  readonly cited_memory_node_id: string | null;
  readonly cited_knowledge_node_id: string | null;
}

export interface DealBriefing {
  readonly deal_id: string;
  readonly generated_at: string;
  readonly status_summary: string;
  readonly causal_diagnosis: readonly CausalDiagnosis[];
  readonly risk_flags: readonly RiskFlag[];
  readonly next_best_actions: readonly NextBestAction[];
  readonly confidence: number;
}

export interface PointInTimeDealState {
  readonly as_of: string;
  readonly deal_memory: DealMemory;
  readonly call_event_ids: readonly string[];
}

export interface DealTimelineResponse {
  readonly deal_id: string;
  readonly tenant_id: string;
  readonly snapshots: readonly DealMemory[];
  readonly point_in_time: PointInTimeDealState | null;
}
