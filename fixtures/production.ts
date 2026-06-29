import type {
  AccountRecord,
  AdminSettingRecord,
  AssistantAnswer,
  AuditEvent,
  CallLibraryRecord,
  CoachingScorecard,
  EngagementTask,
  ExportJob,
  ForecastSubmission,
  RoleRecord,
  UserRecord
} from "@causal-deal/types";

export const accounts = [
  {
    id: "account_northstar",
    tenant_id: "tenant_novaridge",
    record_type: "account",
    name: "Northstar Logistics",
    domain: "northstar.example",
    owner_user_id: "user_maya",
    segment: "Enterprise logistics",
    health: "at_risk",
    renewal_date: null
  },
  {
    id: "account_atlas",
    tenant_id: "tenant_novaridge",
    record_type: "account",
    name: "Atlas Medical Group",
    domain: "atlas.example",
    owner_user_id: "user_owen",
    segment: "Healthcare",
    health: "healthy",
    renewal_date: "2026-03-31"
  }
] satisfies AccountRecord[];

export const roles = [
  {
    id: "role_sales_rep",
    tenant_id: "tenant_novaridge",
    record_type: "role",
    name: "Sales rep",
    permissions: ["deal:read", "call:read", "task:read"]
  },
  {
    id: "role_admin",
    tenant_id: "tenant_novaridge",
    record_type: "role",
    name: "Admin",
    permissions: ["admin:read", "audit:read", "export:read"]
  }
] satisfies RoleRecord[];

export const users = [
  {
    id: "user_maya",
    tenant_id: "tenant_novaridge",
    record_type: "user",
    name: "Maya Chen",
    email: "maya@novaridge.example",
    role_id: "role_sales_rep",
    role_name: "Sales rep",
    manager_id: null,
    status: "active"
  },
  {
    id: "user_owen",
    tenant_id: "tenant_novaridge",
    record_type: "user",
    name: "Owen Patel",
    email: "owen@novaridge.example",
    role_id: "role_sales_rep",
    role_name: "Sales rep",
    manager_id: null,
    status: "active"
  }
] satisfies UserRecord[];

export const adminSettings = [
  {
    id: "admin_setting_exports",
    tenant_id: "tenant_novaridge",
    record_type: "admin_setting",
    key: "exports.enabled",
    value: "true",
    updated_at: "2026-03-04T17:00:00.000Z"
  }
] satisfies AdminSettingRecord[];

export const callLibrary = [
  {
    id: "call_library_ns_005",
    tenant_id: "tenant_novaridge",
    record_type: "call_library_entry",
    call_id: "call_ns_005",
    deal_id: "deal_northstar_expansion",
    account_id: "account_northstar",
    title: "Northstar budget freeze follow-up",
    started_at: "2026-03-04T15:00:00.000Z",
    duration_seconds: 1972,
    primary_rep_id: "user_maya",
    outcome: "budget risk identified",
    recording_url: null,
    transcript_id: "transcript_call_ns_005"
  }
] satisfies CallLibraryRecord[];

export const coachingScorecards = [
  {
    id: "coaching_maya_ns_005",
    tenant_id: "tenant_novaridge",
    record_type: "coaching_scorecard",
    rep_id: "user_maya",
    call_id: "call_ns_005",
    deal_id: "deal_northstar_expansion",
    reviewer_user_id: "user_owen",
    overall_score: 78,
    strengths: ["clear risk recap"],
    improvement_areas: ["secure direct CFO next step"],
    reviewed_at: "2026-03-05T10:00:00.000Z"
  }
] satisfies CoachingScorecard[];

export const forecastSubmissions = [
  {
    id: "forecast_2026_03_maya",
    tenant_id: "tenant_novaridge",
    record_type: "forecast_submission",
    period: "2026-03",
    submitted_by_user_id: "user_maya",
    forecast_category: "best_case",
    commit_amount_usd: 92000,
    best_case_amount_usd: 212000,
    pipeline_amount_usd: 212000,
    submitted_at: "2026-03-04T18:00:00.000Z"
  }
] satisfies ForecastSubmission[];

export const engagementTasks = [
  {
    id: "task_followup_cfo",
    tenant_id: "tenant_novaridge",
    record_type: "engagement_task",
    deal_id: "deal_northstar_expansion",
    account_id: "account_northstar",
    owner_user_id: "user_maya",
    title: "Send revised CFO rollout plan",
    due_date: "2026-03-08",
    priority: "high",
    status: "open",
    source_call_id: "call_ns_005"
  },
  {
    id: "task_atlas_redlines",
    tenant_id: "tenant_novaridge",
    record_type: "engagement_task",
    deal_id: "deal_atlas_renewal",
    account_id: "account_atlas",
    owner_user_id: "user_owen",
    title: "Check procurement redlines",
    due_date: "2026-03-03",
    priority: "medium",
    status: "open",
    source_call_id: "call_at_003"
  }
] satisfies EngagementTask[];

export const assistantAnswers = [
  {
    id: "assistant_answer_northstar_risk",
    tenant_id: "tenant_novaridge",
    record_type: "assistant_answer",
    question: "why is Northstar risky?",
    answer: "Northstar is risky because CFO budget approval stalled after champion silence.",
    citation_ids: ["call_ns_005", "deal_northstar_expansion:deal_memory:2026-03-04T15:00:00.000Z"],
    created_at: "2026-03-04T18:05:00.000Z",
    created_by_user_id: "user_maya"
  }
] satisfies AssistantAnswer[];

export const auditEvents = [
  {
    id: "audit_export_pipeline_snapshot",
    tenant_id: "tenant_novaridge",
    record_type: "audit_event",
    actor_user_id: "user_maya",
    action: "export.created",
    target_type: "export_job",
    target_id: "export_pipeline_snapshot",
    occurred_at: "2026-03-04T18:10:00.000Z"
  }
] satisfies AuditEvent[];

export const exportJobs = [
  {
    id: "export_pipeline_snapshot",
    tenant_id: "tenant_novaridge",
    record_type: "export_job",
    requested_by_user_id: "user_maya",
    export_type: "pipeline_snapshot",
    status: "ready",
    created_at: "2026-03-04T18:09:00.000Z",
    completed_at: "2026-03-04T18:10:00.000Z",
    download_url: "demo://exports/pipeline_snapshot.csv"
  }
] satisfies ExportJob[];
