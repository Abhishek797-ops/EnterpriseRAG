"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { getUser, logout, type UserInfo } from "@/lib/auth";
import RAGDebugPanel, { type DebugData } from "@/components/RAGDebugPanel";
import { apiFetch } from "@/lib/api";

const ARCHITECTURE_NODES = [
    { id: "user", label: "User Input", sub: "Text Query", icon: "👤", color: "#60A5FA" },
    { id: "router", label: "Agentic Router", sub: "Intent Classification", icon: "🔀", color: "#F472B6" },
    { id: "embed", label: "Embedding", sub: "Gemini 1.0 Pro", icon: "🧬", color: "#34D399" },
    { id: "faiss", label: "Vector Search", sub: "Hybrid (FAISS + TF)", icon: "🎯", color: "#A78BFA" },
    { id: "rerank", label: "LLM Reranking", sub: "Cross-Encoder", icon: "⚖️", color: "#FB923C" },
    { id: "llm", label: "Generation", sub: "Gemini 2.5 Flash", icon: "🧠", color: "#FFD700" },
];

export default function RAGDebugPage() {
    const router = useRouter();
    const [user, setUser] = useState<UserInfo | null>(null);
    const [loading, setLoading] = useState(true);

    const [query, setQuery] = useState("");
    const [debugData, setDebugData] = useState<DebugData | null>(null);
    const [isTesting, setIsTesting] = useState(false);
    const [activeNode, setActiveNode] = useState<string | null>(null);
    const [loadingStep, setLoadingStep] = useState<string>("");

    // Auth verification
    useEffect(() => {
        (async () => {
            try {
                const me = await getUser();
                if (me.role !== "admin" && me.role !== "engineer") {
                    router.replace("/dashboard/viewer");
                    return;
                }
                setUser(me);
            } catch {
                router.replace("/");
            } finally {
                setLoading(false);
            }
        })();
    }, [router]);

    const handleTestSequence = async () => {
        if (!query.trim() || isTesting) return;

        setIsTesting(true);
        setDebugData(null);
        setActiveNode("user");

        try {
            // Simulated visual sequence for the diagram
            await new Promise((r) => setTimeout(r, 600));
            setActiveNode("router");
            await new Promise((r) => setTimeout(r, 600));
            setActiveNode("embed");
            setLoadingStep("embedding");
            await new Promise((r) => setTimeout(r, 600));
            setActiveNode("faiss");
            setLoadingStep("searching");
            await new Promise((r) => setTimeout(r, 600));
            setLoadingStep("retrieving");
            await new Promise((r) => setTimeout(r, 400));
            setActiveNode("rerank");
            setLoadingStep("reranking");
            await new Promise((r) => setTimeout(r, 800));
            setActiveNode("llm");
            setLoadingStep("generating");

            // Actual backend call
            const data = await apiFetch<{ answer: string; debug: DebugData }>("/api/chat/debug", {
                method: "POST",
                body: JSON.stringify({ question: query }),
            });

            setDebugData(data.debug);
            setLoadingStep("");
            setActiveNode(null);
        } catch (error) {
            console.error(error);
            setActiveNode(null);
            setLoadingStep("");
        } finally {
            setIsTesting(false);
        }
    };

    if (loading) return null;

    return (
        <div className="min-h-screen bg-pagani-black text-white p-6 md:p-12 font-sans selection:bg-pagani-gold/30">
            {/* Header */}
            <header className="max-w-7xl mx-auto flex items-center justify-between mb-12 border-b border-white/5 pb-6">
                <div>
                    <h1
                        className="text-2xl md:text-3xl font-bold uppercase tracking-tight text-white mb-1"
                        style={{ fontFamily: "var(--font-orbitron)" }}
                    >
                        Pagani <span className="text-pagani-gold">Enterprise RAG</span> Arch.
                    </h1>
                    <p className="text-xs text-gray-500 uppercase tracking-widest">
                        Debug & Architecture Visualization Console
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right hidden sm:block">
                        <p className="text-xs font-semibold text-white">{user?.username}</p>
                        <p className="text-[10px] text-pagani-gold uppercase tracking-widest">
                            {user?.role} Access
                        </p>
                    </div>
                    <button
                        onClick={() => router.push(`/dashboard/${user?.role}`)}
                        className="px-4 py-2 border border-white/10 rounded-lg text-xs uppercase hover:bg-white/5 transition-colors"
                    >
                        Return to Dashboard
                    </button>
                </div>
            </header>

            <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-10">
                {/* Left Column: Flow Diagram & Metrics */}
                <div className="space-y-8">
                    {/* Architecture Flow Diagram */}
                    <div
                        className="p-8 rounded-2xl border border-white/10 relative overflow-hidden"
                        style={{
                            background: "linear-gradient(135deg, rgba(20,20,20,0.8) 0%, rgba(10,10,10,0.95) 100%)",
                            boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
                        }}
                    >
                        {/* Background Grid Accent */}
                        <div
                            className="absolute inset-0 opacity-10 pointer-events-none"
                            style={{
                                backgroundImage: `radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)`,
                                backgroundSize: "24px 24px",
                            }}
                        />

                        <h2 className="text-xs text-pagani-gold uppercase tracking-widest mb-8 flex items-center gap-3">
                            <span className="w-2 h-2 rounded-full bg-pagani-gold animate-pulse" />
                            Live System Pipeline
                        </h2>

                        <div className="flex flex-col gap-4 relative z-10">
                            {ARCHITECTURE_NODES.map((node, i) => (
                                <div key={node.id} className="relative">
                                    <motion.div
                                        className={`p-4 rounded-xl border flex items-center gap-4 transition-all duration-300 ${activeNode === node.id
                                            ? "bg-white/10 scale-105 shadow-[0_0_20px_rgba(255,215,0,0.15)]"
                                            : "bg-black/40 border-white/5 hover:border-white/10"
                                            }`}
                                        style={{
                                            borderColor: activeNode === node.id ? node.color : "rgba(255,255,255,0.05)",
                                        }}
                                        animate={{
                                            boxShadow:
                                                activeNode === node.id
                                                    ? `0 0 20px ${node.color}30`
                                                    : "none",
                                        }}
                                    >
                                        <div
                                            className="w-12 h-12 rounded-lg flex items-center justify-center text-xl shrink-0"
                                            style={{
                                                backgroundColor: `${node.color}15`,
                                                border: `1px solid ${node.color}30`,
                                                color: node.color,
                                            }}
                                        >
                                            {node.icon}
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-semibold text-white tracking-wide">
                                                {node.label}
                                            </h3>
                                            <p className="text-xs text-gray-400 mt-0.5">{node.sub}</p>
                                        </div>
                                    </motion.div>

                                    {/* Connection Line */}
                                    {i < ARCHITECTURE_NODES.length - 1 && (
                                        <div className="h-6 flex justify-center py-1">
                                            <div className="w-0.5 h-full bg-white/5 relative">
                                                <AnimatePresence>
                                                    {activeNode && ARCHITECTURE_NODES.findIndex(n => n.id === activeNode) > i && (
                                                        <motion.div
                                                            initial={{ height: 0 }}
                                                            animate={{ height: "100%" }}
                                                            className="absolute top-0 w-full"
                                                            style={{ backgroundColor: node.color }}
                                                        />
                                                    )}
                                                </AnimatePresence>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Stats Dashboard */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02]">
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-2">
                                Vector Database
                            </p>
                            <p className="text-2xl text-white font-mono">FAISS CPU</p>
                            <p className="text-xs text-emerald-400 mt-1">20,000+ chunks</p>
                        </div>
                        <div className="p-5 rounded-xl border border-white/5 bg-white/[0.02]">
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-2">
                                Embedded Model
                            </p>
                            <p className="text-2xl text-white font-mono">Gemini 1.0</p>
                            <p className="text-xs text-emerald-400 mt-1">768 dimensions</p>
                        </div>
                    </div>
                </div>

                {/* Right Column: Interactive Test Console */}
                <div className="flex flex-col h-full space-y-4">
                    <div
                        className="rounded-xl border border-white/10 bg-black/50 p-6 flex flex-col flex-1"
                        style={{ backdropFilter: "blur(12px)" }}
                    >
                        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-white/10 pb-4">
                            Pipeline Inspector
                        </h2>

                        {/* Query Input */}
                        <div className="relative mb-6">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter technical query to trace..."
                                disabled={isTesting}
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white focus:outline-none focus:border-pagani-gold transition-colors disabled:opacity-50"
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") handleTestSequence();
                                }}
                            />
                            <button
                                onClick={handleTestSequence}
                                disabled={!query.trim() || isTesting}
                                className="absolute right-2 top-2 bottom-2 px-6 rounded-md bg-pagani-gold text-black text-xs font-bold uppercase tracking-wider hover:bg-yellow-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isTesting ? "Tracing..." : "Trace"}
                            </button>
                        </div>

                        {/* Interactive Results Area */}
                        <div className="flex-1 overflow-y-auto">
                            {!isTesting && !debugData && (
                                <div className="h-full flex flex-col items-center justify-center text-center px-6 opacity-40">
                                    <div className="w-16 h-16 mb-4 rounded-full border-2 border-dashed border-white flex flex-col items-center justify-center text-2xl">
                                        🔍
                                    </div>
                                    <p className="text-sm text-white font-medium">Ready for trace</p>
                                    <p className="text-xs text-gray-400 mt-2">
                                        Run a query to inspect vector search scores, context retrieval, and generation timings.
                                    </p>
                                </div>
                            )}

                            {isTesting && (
                                <div className="mt-8 relative">
                                    <div className="flex flex-col items-center justify-center space-y-4">
                                        <motion.div
                                            animate={{ rotate: 360 }}
                                            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                                            className="w-12 h-12 border-2 border-pagani-gold/20 border-t-pagani-gold rounded-full"
                                        />
                                        <p className="text-xs text-pagani-gold uppercase tracking-[0.2em] animate-pulse">
                                            Tracing Pipeline Execution
                                        </p>
                                    </div>

                                    {/* Render the RAG debug panel loading steps inline */}
                                    <div className="mt-8">
                                        <RAGDebugPanel debug={null} isLoading={true} loadingStep={loadingStep} />
                                    </div>
                                </div>
                            )}

                            {debugData && !isTesting && (
                                <div className="space-y-4">
                                    <h3 className="text-xs text-pagani-gold uppercase tracking-widest font-semibold pb-2 border-b border-white/10">
                                        Trace Complete
                                    </h3>

                                    {/* The extracted debug panel component */}
                                    <div className="block">
                                        <RAGDebugPanel debug={debugData} />
                                    </div>

                                    {/* Expanded Router Decision specifically for this arch page */}
                                    {debugData.router_decision && (
                                        <div className="mt-6 p-4 rounded-lg bg-indigo-900/10 border border-indigo-500/20">
                                            <p className="text-xs text-indigo-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                                                <span className="text-base">🔀</span> Router Routing Decision
                                            </p>
                                            <pre className="text-[10px] text-gray-300 font-mono bg-black/40 p-3 rounded-md overflow-x-auto">
                                                {JSON.stringify(debugData.router_decision, null, 2)}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
