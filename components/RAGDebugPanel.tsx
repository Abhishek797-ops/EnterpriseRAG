"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

/* ═══════════════════════════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════════════════════════ */

interface PipelineStep {
    step: string;
    label: string;
    timestamp_ms: number;
}

interface SearchResult {
    source: string;
    similarity: number;
    chunk_preview: string;
}

interface RetrievedChunk {
    source: string;
    content: string;
    relevance_score: number;
}

interface DebugTiming {
    embedding_ms?: number;
    search_ms?: number;
    reranking_ms?: number;
    generation_ms?: number;
    total_ms?: number;
}

export interface DebugData {
    pipeline_steps: PipelineStep[];
    search_results: SearchResult[];
    retrieved_chunks: RetrievedChunk[];
    timing: DebugTiming;
    router_decision: Record<string, unknown> | null;
}

interface RAGDebugPanelProps {
    debug: DebugData | null;
    isLoading?: boolean;
    loadingStep?: string;
}

/* ═══════════════════════════════════════════════════════════════
   LOADING STEPS ANIMATION
   ═══════════════════════════════════════════════════════════════ */

export function DebugLoadingSteps({ step }: { step: string }) {
    const steps = [
        { key: "embedding", label: "Embedding Query...", icon: "⟐" },
        { key: "searching", label: "Searching Vector Database...", icon: "◉" },
        { key: "retrieving", label: "Retrieving Documents...", icon: "◈" },
        { key: "reranking", label: "Reranking with LLM...", icon: "⬡" },
        { key: "generating", label: "Generating AI Response...", icon: "◆" },
    ];

    const currentIdx = steps.findIndex((s) => s.key === step);

    return (
        <div className="space-y-2 py-3">
            {steps.map((s, i) => {
                const isComplete = i < currentIdx;
                const isActive = i === currentIdx;
                const isPending = i > currentIdx;

                return (
                    <motion.div
                        key={s.key}
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.08, duration: 0.25 }}
                        className="flex items-center gap-3"
                    >
                        <div className="w-5 text-center">
                            {isComplete && (
                                <motion.span
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    className="text-emerald-400 text-xs"
                                >
                                    ✔
                                </motion.span>
                            )}
                            {isActive && (
                                <motion.span
                                    animate={{ opacity: [0.3, 1, 0.3] }}
                                    transition={{ repeat: Infinity, duration: 1.2 }}
                                    className="text-[#FFD700] text-xs"
                                >
                                    {s.icon}
                                </motion.span>
                            )}
                            {isPending && (
                                <span className="text-gray-600 text-xs">○</span>
                            )}
                        </div>
                        <span
                            className={`text-xs tracking-wide ${isComplete
                                ? "text-emerald-400/80"
                                : isActive
                                    ? "text-[#FFD700] font-medium"
                                    : "text-gray-600"
                                }`}
                        >
                            {isComplete ? s.label.replace("...", "") : s.label}
                        </span>
                        {isComplete && s.key === "embedding" && (
                            <span className="text-[9px] text-gray-600 ml-auto">done</span>
                        )}
                    </motion.div>
                );
            })}
        </div>
    );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN DEBUG PANEL
   ═══════════════════════════════════════════════════════════════ */

export default function RAGDebugPanel({ debug, isLoading, loadingStep }: RAGDebugPanelProps) {
    const [expanded, setExpanded] = useState(false);
    const [activeTab, setActiveTab] = useState<"pipeline" | "search" | "chunks" | "timing">("pipeline");
    const [expandedChunk, setExpandedChunk] = useState<number | null>(null);

    if (isLoading && loadingStep) {
        return (
            <div
                className="mt-3 rounded-xl p-4 border border-[#FFD700]/15"
                style={{
                    background: "linear-gradient(145deg, rgba(15,15,15,0.9) 0%, rgba(8,8,8,0.95) 100%)",
                }}
            >
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-[#FFD700] animate-pulse" />
                    <span
                        className="text-[10px] text-[#FFD700]/70 uppercase tracking-[0.2em] font-bold"
                        style={{ fontFamily: "var(--font-orbitron, monospace)" }}
                    >
                        AI Processing Steps
                    </span>
                </div>
                <DebugLoadingSteps step={loadingStep} />
            </div>
        );
    }

    if (!debug) return null;

    const tabs = [
        { key: "pipeline" as const, label: "Pipeline" },
        { key: "search" as const, label: "Search Results" },
        { key: "chunks" as const, label: "Chunks" },
        { key: "timing" as const, label: "Timeline" },
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="mt-3"
        >
            {/* Collapsible Header */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between py-2.5 px-4 rounded-xl border border-white/5 hover:border-[#FFD700]/20 transition-all group"
                style={{
                    background: expanded
                        ? "linear-gradient(145deg, rgba(20,20,20,0.9) 0%, rgba(10,10,10,0.95) 100%)"
                        : "rgba(15,15,15,0.6)",
                }}
            >
                <div className="flex items-center gap-2.5">
                    <span className="text-[10px] text-[#FFD700]/50 group-hover:text-[#FFD700]/80 transition-colors">
                        {expanded ? "▼" : "▶"}
                    </span>
                    <span
                        className="text-[10px] text-[#FFD700]/60 uppercase tracking-[0.2em] group-hover:text-[#FFD700]/90 transition-colors font-bold"
                        style={{ fontFamily: "var(--font-orbitron, monospace)" }}
                    >
                        Show AI Reasoning
                    </span>
                </div>
                <div className="flex items-center gap-3">
                    {debug.timing.total_ms && (
                        <span className="text-[9px] text-gray-600">
                            {(debug.timing.total_ms / 1000).toFixed(1)}s total
                        </span>
                    )}
                    <span className="text-[9px] text-emerald-500/60">
                        {debug.pipeline_steps.length} steps
                    </span>
                </div>
            </button>

            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                    >
                        <div
                            className="rounded-b-xl border border-t-0 border-white/5 p-4"
                            style={{
                                background:
                                    "linear-gradient(145deg, rgba(15,15,15,0.95) 0%, rgba(8,8,8,0.98) 100%)",
                            }}
                        >
                            {/* Tab Bar */}
                            <div className="flex gap-1 mb-4 p-1 rounded-lg bg-black/40">
                                {tabs.map((tab) => (
                                    <button
                                        key={tab.key}
                                        onClick={() => setActiveTab(tab.key)}
                                        className={`flex-1 text-[10px] py-1.5 rounded-md uppercase tracking-wider font-medium transition-all ${activeTab === tab.key
                                            ? "bg-[#FFD700]/15 text-[#FFD700] border border-[#FFD700]/20"
                                            : "text-gray-500 hover:text-gray-300 border border-transparent"
                                            }`}
                                    >
                                        {tab.label}
                                    </button>
                                ))}
                            </div>

                            {/* Pipeline Steps Tab */}
                            {activeTab === "pipeline" && (
                                <div className="space-y-2">
                                    {debug.pipeline_steps.map((step, i) => (
                                        <motion.div
                                            key={step.step}
                                            initial={{ opacity: 0, x: -12 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.06, duration: 0.3 }}
                                            className="flex items-center justify-between py-2 px-3 rounded-lg bg-white/[0.02] border border-white/[0.03]"
                                        >
                                            <div className="flex items-center gap-3">
                                                <span className="text-emerald-400 text-xs">✔</span>
                                                <span className="text-xs text-gray-300">
                                                    {step.label}
                                                </span>
                                            </div>
                                            <span className="text-[10px] text-gray-600 font-mono">
                                                {step.timestamp_ms}ms
                                            </span>
                                        </motion.div>
                                    ))}
                                </div>
                            )}

                            {/* Search Results Tab */}
                            {activeTab === "search" && (
                                <div className="space-y-2">
                                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3 font-medium">
                                        Top Retrieved Documents
                                    </p>
                                    {debug.search_results.length === 0 && (
                                        <p className="text-xs text-gray-600 italic">No vector search performed.</p>
                                    )}
                                    {debug.search_results.map((res, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, y: 6 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.05, duration: 0.25 }}
                                            className="p-3 rounded-lg border border-white/[0.04] bg-white/[0.015]"
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-xs text-white font-medium truncate max-w-[200px]">
                                                    {i + 1}. {res.source}
                                                </span>
                                                <span className="text-[10px] font-mono text-[#FFD700]">
                                                    {res.similarity.toFixed(2)}
                                                </span>
                                            </div>
                                            {/* Similarity Bar */}
                                            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                <motion.div
                                                    className="h-full rounded-full"
                                                    style={{
                                                        background:
                                                            "linear-gradient(90deg, #D4AF37, #FFD700)",
                                                    }}
                                                    initial={{ width: 0 }}
                                                    animate={{
                                                        width: `${Math.max(res.similarity * 100, 5)}%`,
                                                    }}
                                                    transition={{
                                                        delay: 0.2 + i * 0.1,
                                                        duration: 0.6,
                                                        ease: "easeOut",
                                                    }}
                                                />
                                            </div>
                                            <p className="text-[10px] text-gray-600 mt-2 line-clamp-2 leading-relaxed">
                                                {res.chunk_preview}
                                            </p>
                                        </motion.div>
                                    ))}
                                </div>
                            )}

                            {/* Chunks Tab */}
                            {activeTab === "chunks" && (
                                <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1 scrollbar-thin">
                                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3 font-medium">
                                        Retrieved Context Chunks
                                    </p>
                                    {debug.retrieved_chunks.length === 0 && (
                                        <p className="text-xs text-gray-600 italic">No chunks retrieved.</p>
                                    )}
                                    {debug.retrieved_chunks.map((chunk, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, y: 6 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                            className="rounded-lg border border-white/[0.04] bg-white/[0.015] overflow-hidden"
                                        >
                                            <button
                                                onClick={() =>
                                                    setExpandedChunk(expandedChunk === i ? null : i)
                                                }
                                                className="w-full flex items-center justify-between p-3 hover:bg-white/[0.02] transition-colors"
                                            >
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[10px] text-[#FFD700]/50">
                                                        {expandedChunk === i ? "▼" : "▶"}
                                                    </span>
                                                    <span className="text-xs text-white font-medium">
                                                        Chunk {i + 1}
                                                    </span>
                                                    <span className="text-[10px] text-gray-500 truncate max-w-[150px]">
                                                        {chunk.source}
                                                    </span>
                                                </div>
                                                <span
                                                    className="text-[9px] px-2 py-0.5 rounded-full font-mono"
                                                    style={{
                                                        background:
                                                            chunk.relevance_score >= 70
                                                                ? "rgba(34,197,94,0.1)"
                                                                : "rgba(234,179,8,0.1)",
                                                        color:
                                                            chunk.relevance_score >= 70
                                                                ? "#4ade80"
                                                                : "#facc15",
                                                        border:
                                                            chunk.relevance_score >= 70
                                                                ? "1px solid rgba(34,197,94,0.2)"
                                                                : "1px solid rgba(234,179,8,0.2)",
                                                    }}
                                                >
                                                    Score: {chunk.relevance_score}
                                                </span>
                                            </button>
                                            <AnimatePresence>
                                                {expandedChunk === i && (
                                                    <motion.div
                                                        initial={{ height: 0 }}
                                                        animate={{ height: "auto" }}
                                                        exit={{ height: 0 }}
                                                        className="overflow-hidden"
                                                    >
                                                        <div className="px-3 pb-3 border-t border-white/[0.03]">
                                                            <p className="text-[10px] text-gray-500 mt-2 mb-1 uppercase tracking-wider">
                                                                Source: {chunk.source}
                                                            </p>
                                                            <div className="bg-black/40 rounded-md p-3">
                                                                <p className="text-[11px] text-gray-400 whitespace-pre-wrap leading-relaxed font-mono">
                                                                    {chunk.content}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </motion.div>
                                    ))}
                                </div>
                            )}

                            {/* Timing Tab */}
                            {activeTab === "timing" && (
                                <div className="space-y-3">
                                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3 font-medium">
                                        Processing Timeline
                                    </p>
                                    {[
                                        { label: "Query Embedding", ms: debug.timing.embedding_ms, color: "#38BDF8" },
                                        { label: "Vector Search", ms: debug.timing.search_ms, color: "#A78BFA" },
                                        { label: "LLM Reranking", ms: debug.timing.reranking_ms, color: "#FB923C" },
                                        { label: "LLM Generation", ms: debug.timing.generation_ms, color: "#FFD700" },
                                    ]
                                        .filter((t) => t.ms !== undefined)
                                        .map((t, i) => {
                                            const maxMs = debug.timing.total_ms || 1;
                                            const pct = Math.max(((t.ms ?? 0) / maxMs) * 100, 3);
                                            return (
                                                <motion.div
                                                    key={t.label}
                                                    initial={{ opacity: 0, x: -8 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: i * 0.08, duration: 0.3 }}
                                                >
                                                    <div className="flex justify-between items-center mb-1">
                                                        <span className="text-xs text-gray-300">
                                                            {t.label}
                                                        </span>
                                                        <span className="text-[10px] text-gray-500 font-mono">
                                                            {(t.ms ?? 0) >= 1000
                                                                ? `${((t.ms ?? 0) / 1000).toFixed(1)}s`
                                                                : `${t.ms}ms`}
                                                        </span>
                                                    </div>
                                                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                                        <motion.div
                                                            className="h-full rounded-full"
                                                            style={{ background: t.color }}
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${pct}%` }}
                                                            transition={{
                                                                delay: 0.3 + i * 0.12,
                                                                duration: 0.6,
                                                                ease: "easeOut",
                                                            }}
                                                        />
                                                    </div>
                                                </motion.div>
                                            );
                                        })}

                                    {/* Total */}
                                    {debug.timing.total_ms && (
                                        <div className="mt-2 pt-3 border-t border-white/5 flex justify-between items-center">
                                            <span className="text-xs text-white font-medium">
                                                Total Latency
                                            </span>
                                            <span
                                                className="text-xs text-[#FFD700] font-bold font-mono"
                                                style={{ fontFamily: "var(--font-orbitron, monospace)" }}
                                            >
                                                {(debug.timing.total_ms / 1000).toFixed(2)}s
                                            </span>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
