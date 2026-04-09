/**
 * Enterprise RAG — Shared Constants
 * Badge color map for SSE event types and chunk types.
 * Import from here — never hardcode colors inline.
 */

// ── SSE Event Type Badge Colors ──
export const EVENT_TYPE_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  planner:    { bg: "bg-purple-500/20", text: "text-purple-400", label: "Planner" },
  retrieval:  { bg: "bg-blue-500/20",   text: "text-blue-400",   label: "Retrieval" },
  chunks:     { bg: "bg-teal-500/20",   text: "text-teal-400",   label: "Chunks" },
  router:     { bg: "bg-amber-500/20",  text: "text-amber-400",  label: "Router" },
  agent:      { bg: "bg-indigo-500/20", text: "text-indigo-400", label: "Agent" },
  thinking:   { bg: "bg-gray-500/20",   text: "text-gray-400",   label: "Thinking" },
  cost:       { bg: "bg-green-500/20",  text: "text-green-400",  label: "Cost" },
  evaluation: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "Eval" },
  gatekeeper: { bg: "bg-red-500/20",    text: "text-red-400",    label: "Gatekeeper" },
  progress:   { bg: "bg-sky-500/20",    text: "text-sky-400",    label: "Progress" },
  token:      { bg: "bg-white/10",      text: "text-white/60",   label: "Token" },
  result:     { bg: "bg-emerald-500/20",text: "text-emerald-400",label: "Result" },
  error:      { bg: "bg-red-600/20",    text: "text-red-500",    label: "Error" },
  done:       { bg: "bg-emerald-500/20",text: "text-emerald-400",label: "Done" },
  step:       { bg: "bg-sky-500/20",    text: "text-sky-400",    label: "Step" },
  chunk_done: { bg: "bg-teal-500/20",   text: "text-teal-400",   label: "Chunk" },
} as const;

// ── Chunk Type Badge Colors ──
export const CHUNK_TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  body:           { bg: "bg-slate-500/20",  text: "text-slate-400" },
  table:          { bg: "bg-cyan-500/20",   text: "text-cyan-400" },
  code:           { bg: "bg-violet-500/20", text: "text-violet-400" },
  image_caption:  { bg: "bg-pink-500/20",   text: "text-pink-400" },
} as const;

// ── Document Type Badge Colors ──
export const DOC_TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  narrative:      { bg: "bg-blue-500/20",   text: "text-blue-400" },
  "table-heavy":  { bg: "bg-cyan-500/20",   text: "text-cyan-400" },
  "code-dominant":{ bg: "bg-violet-500/20", text: "text-violet-400" },
  mixed:          { bg: "bg-amber-500/20",  text: "text-amber-400" },
} as const;

// ── Pipeline Step Icons (label + icon name mapping) ──
export const PIPELINE_STEPS = [
  { step: 1, label: "Planning",   icon: "brain" },
  { step: 2, label: "Retrieving", icon: "search" },
  { step: 3, label: "Analysing",  icon: "agents" },
  { step: 4, label: "Writing",    icon: "pen" },
] as const;

// ── Score Color Thresholds ──
export function getScoreColor(score: number): string {
  if (score >= 0.80) return "text-green-400";
  if (score >= 0.60) return "text-yellow-400";
  return "text-red-400";
}

export function getScoreBg(score: number): string {
  if (score >= 0.80) return "bg-green-500/20";
  if (score >= 0.60) return "bg-yellow-500/20";
  return "bg-red-500/20";
}

// ── SSE Event Type ──
export interface SSEEvent {
  timestamp: string;
  event_type: string;
  payload: Record<string, unknown>;
  human_readable: string;
}

// ── Human-readable SSE event formatter ──
export function formatSSEEvent(eventType: string, payload: Record<string, unknown>): string {
  switch (eventType) {
    case "planner":
      return `Strategy: ${payload.strategy} — ${(payload.sub_queries as string[])?.length || 0} sub-queries planned (complexity: ${payload.complexity}) [${payload.duration_ms}ms]`;
    case "retrieval":
      return `Retrieved ${payload.chunks_found} chunks via ${payload.tool} — top score: ${payload.top_score} [${payload.duration_ms}ms]`;
    case "chunks":
      return `Context locked: ${(payload.chunks as unknown[])?.length || 0} chunks`;
    case "router":
      return `Routed to ${payload.routed_to} (confidence: ${payload.confidence})`;
    case "agent": {
      const name = payload.name || `Agent ${payload.agent}`;
      if (payload.status === "started") return `${name} started${payload.input_chunks ? ` — ${payload.input_chunks} input chunks` : ""}`;
      return `${name} done${payload.output_chunks ? ` — ${payload.output_chunks} chunks kept` : ""}${payload.removed_duplicates ? `, ${payload.removed_duplicates} duplicates removed` : ""} [${payload.duration_ms}ms]`;
    }
    case "thinking":
      return `Analyst reasoning: ${payload.thought}`;
    case "cost":
      return `Query complete — ${payload.gemini_calls} Gemini calls, $${payload.estimated_cost_usd}, ${payload.total_latency_ms}ms total`;
    case "evaluation":
      return `Eval scores: F=${payload.faithfulness} R=${payload.relevance} C=${payload.completeness}`;
    case "gatekeeper":
      return payload.flagged ? `⚠ Flagged: ${payload.reason} (confidence: ${payload.confidence})` : "✓ Passed gatekeeper check";
    case "progress":
      return `Step ${payload.step}: ${payload.label}`;
    case "token":
      return String(payload.token || "");
    case "done":
      return `✓ Complete (confidence: ${payload.confidence}, strategy: ${payload.strategy})`;
    case "error":
      return `✗ Error: ${payload.message}`;
    default:
      return JSON.stringify(payload).slice(0, 120);
  }
}
