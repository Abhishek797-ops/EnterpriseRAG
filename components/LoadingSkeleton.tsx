"use client";

import React from "react";

interface SkeletonProps {
  /** Width of the skeleton. Default: "100%" */
  width?: string;
  /** Height of the skeleton. Default: "20px" */
  height?: string;
  /** Border radius. Default: "8px" */
  borderRadius?: string;
  /** Number of skeleton rows. Default: 1 */
  rows?: number;
  /** Gap between rows. Default: "12px" */
  gap?: string;
  /** Custom className */
  className?: string;
}

/**
 * Reusable loading skeleton component with shimmer animation.
 * Supports single line, multi-line, and card layouts.
 */
export function LoadingSkeleton({
  width = "100%",
  height = "20px",
  borderRadius = "8px",
  rows = 1,
  gap = "12px",
  className = "",
}: SkeletonProps) {
  return (
    <div className={className} style={{ display: "flex", flexDirection: "column", gap }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton-shimmer"
          style={{
            width: i === rows - 1 && rows > 1 ? "70%" : width,
            height,
            borderRadius,
            background: "linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.04) 75%)",
            backgroundSize: "200% 100%",
            animation: "shimmer 1.5s ease-in-out infinite",
          }}
        />
      ))}
      <style jsx>{`
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}

/**
 * Card-style loading skeleton for dashboard widgets.
 */
export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div
      className={className}
      style={{
        padding: "24px",
        borderRadius: "16px",
        background: "rgba(255,255,255,0.03)",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <LoadingSkeleton width="40%" height="14px" />
      <div style={{ marginTop: "16px" }}>
        <LoadingSkeleton width="60%" height="32px" borderRadius="6px" />
      </div>
      <div style={{ marginTop: "16px" }}>
        <LoadingSkeleton rows={3} height="12px" gap="8px" />
      </div>
    </div>
  );
}

/**
 * Table-style loading skeleton for data tables.
 */
export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
      {/* Header */}
      <div style={{ display: "flex", gap: "16px", paddingBottom: "8px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        {Array.from({ length: cols }).map((_, i) => (
          <LoadingSkeleton key={`h-${i}`} width={`${100 / cols}%`} height="16px" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, row) => (
        <div key={`r-${row}`} style={{ display: "flex", gap: "16px", padding: "8px 0" }}>
          {Array.from({ length: cols }).map((_, col) => (
            <LoadingSkeleton key={`c-${row}-${col}`} width={`${100 / cols}%`} height="14px" />
          ))}
        </div>
      ))}
    </div>
  );
}

export default LoadingSkeleton;
