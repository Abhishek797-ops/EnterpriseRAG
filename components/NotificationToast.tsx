"use client";

import React, { useState, useEffect, useCallback, createContext, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";

// ── Types ──
type ToastLevel = "info" | "success" | "warning" | "error";

interface Toast {
  id: string;
  title: string;
  body: string;
  level: ToastLevel;
  duration?: number; // ms, default 5000
}

interface ToastContextType {
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
}

// ── Context ──
const ToastContext = createContext<ToastContextType | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a ToastProvider");
  return ctx;
}

// ── Level Colors & Icons ──
const LEVEL_STYLES: Record<ToastLevel, { bg: string; border: string; icon: string }> = {
  info: { bg: "rgba(59,130,246,0.1)", border: "rgba(59,130,246,0.3)", icon: "ℹ️" },
  success: { bg: "rgba(34,197,94,0.1)", border: "rgba(34,197,94,0.3)", icon: "✅" },
  warning: { bg: "rgba(234,179,8,0.1)", border: "rgba(234,179,8,0.3)", icon: "⚠️" },
  error: { bg: "rgba(239,68,68,0.1)", border: "rgba(239,68,68,0.3)", icon: "❌" },
};

// ── Toast Provider ──
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setToasts((prev) => [...prev, { ...toast, id }]);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      {/* Toast Container */}
      <div
        style={{
          position: "fixed",
          top: "24px",
          right: "24px",
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          maxWidth: "400px",
        }}
      >
        <AnimatePresence>
          {toasts.map((toast) => (
            <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

// ── Individual Toast ──
function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const style = LEVEL_STYLES[toast.level];
  const duration = toast.duration ?? 5000;

  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <motion.div
      initial={{ opacity: 0, x: 100, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.9 }}
      transition={{ type: "spring", damping: 20, stiffness: 300 }}
      style={{
        background: style.bg,
        border: `1px solid ${style.border}`,
        borderRadius: "12px",
        padding: "16px",
        backdropFilter: "blur(16px)",
        cursor: "pointer",
        position: "relative",
        overflow: "hidden",
      }}
      onClick={onClose}
    >
      {/* Progress bar */}
      <motion.div
        initial={{ scaleX: 1 }}
        animate={{ scaleX: 0 }}
        transition={{ duration: duration / 1000, ease: "linear" }}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "3px",
          background: style.border,
          transformOrigin: "left",
        }}
      />

      <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
        <span style={{ fontSize: "18px" }}>{style.icon}</span>
        <div style={{ flex: 1 }}>
          <p style={{ fontWeight: 600, fontSize: "14px", color: "#fff", margin: 0 }}>
            {toast.title}
          </p>
          <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.7)", margin: "4px 0 0" }}>
            {toast.body}
          </p>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onClose(); }}
          style={{
            background: "none",
            border: "none",
            color: "rgba(255,255,255,0.5)",
            cursor: "pointer",
            fontSize: "16px",
            padding: "0",
            lineHeight: 1,
          }}
        >
          ×
        </button>
      </div>
    </motion.div>
  );
}

export default ToastProvider;
