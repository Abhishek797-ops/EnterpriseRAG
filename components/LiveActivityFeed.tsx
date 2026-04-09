"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { EVENT_TYPE_COLORS, type SSEEvent } from "@/lib/constants";

interface LiveActivityFeedProps {
  events: SSEEvent[];
  title?: string;
  height?: string;
  onClear?: () => void;
}

export default function LiveActivityFeed({
  events,
  title = "Backend Activity",
  height = "h-96",
  onClear,
}: LiveActivityFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const prefersReducedMotion =
    typeof window !== "undefined"
      ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
      : false;

  // Auto-scroll to bottom as new events arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth" });
  }, [events.length, prefersReducedMotion]);

  return (
    <div className="bg-black/80 rounded-xl border border-white/10 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-semibold tracking-wider uppercase text-white/80">
            {title}
          </span>
          <span className="text-[10px] text-white/40 ml-1">{events.length} events</span>
        </div>
        {onClear && (
          <button
            onClick={onClear}
            className="text-[10px] text-white/40 hover:text-white/70 uppercase tracking-wider transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Event feed */}
      <div className={`${height} overflow-y-auto px-3 py-2 space-y-0.5 scrollbar-thin`}>
        {events.length === 0 && (
          <div className="flex items-center justify-center h-full text-white/20 text-xs">
            Waiting for events…
          </div>
        )}
        <AnimatePresence initial={false}>
          {events.map((event, idx) => {
            const colorCfg = EVENT_TYPE_COLORS[event.event_type] || {
              bg: "bg-white/10",
              text: "text-white/50",
              label: event.event_type,
            };
            return (
              <motion.div
                key={`${event.timestamp}-${idx}`}
                initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.15 }}
                className="flex items-start gap-2 py-1 border-b border-white/5 last:border-0"
              >
                {/* Timestamp */}
                <span className="text-[10px] font-mono text-white/30 whitespace-nowrap mt-0.5 shrink-0">
                  {event.timestamp}
                </span>

                {/* Badge */}
                <span
                  className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${colorCfg.bg} ${colorCfg.text} whitespace-nowrap shrink-0`}
                >
                  {colorCfg.label}
                </span>

                {/* Message */}
                <span className="text-xs text-white/70 break-words min-w-0">
                  {event.human_readable}
                </span>
              </motion.div>
            );
          })}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
