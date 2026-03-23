"use client";

import React, { Component, ReactNode } from "react";
import { motion } from "framer-motion";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: string;
}

/**
 * React Error Boundary with a premium fallback UI.
 * Catches JavaScript errors in child components, logs them,
 * and displays a user-friendly error screen with a retry button.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: "" };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[ErrorBoundary] Caught error:", error, errorInfo);
    this.setState({ errorInfo: errorInfo.componentStack || "" });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: "" });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-md w-full text-center p-8 rounded-2xl"
            style={{
              background: "linear-gradient(135deg, rgba(255, 50, 50, 0.05), rgba(255, 100, 50, 0.05))",
              border: "1px solid rgba(255, 80, 80, 0.2)",
              backdropFilter: "blur(12px)",
            }}
          >
            {/* Error icon */}
            <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center"
              style={{ background: "rgba(255, 80, 80, 0.15)" }}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#ff5050" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>

            <h3 className="text-xl font-bold mb-2" style={{ color: "#ff6b6b" }}>
              Something went wrong
            </h3>
            <p className="text-sm opacity-70 mb-6" style={{ color: "#ccc" }}>
              {this.state.error?.message || "An unexpected error occurred."}
            </p>

            <button
              onClick={this.handleRetry}
              className="px-6 py-2.5 rounded-xl font-semibold text-sm transition-all duration-200"
              style={{
                background: "linear-gradient(135deg, #ff5050, #ff8c00)",
                color: "#fff",
                border: "none",
                cursor: "pointer",
              }}
              onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
              onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
            >
              Try Again
            </button>

            {/* Debug info (development only) */}
            {process.env.NODE_ENV === "development" && this.state.errorInfo && (
              <details className="mt-4 text-left text-xs" style={{ color: "#999" }}>
                <summary className="cursor-pointer">Stack Trace</summary>
                <pre className="mt-2 p-3 rounded-lg overflow-auto max-h-48"
                  style={{ background: "rgba(0,0,0,0.3)", fontSize: "10px" }}>
                  {this.state.errorInfo}
                </pre>
              </details>
            )}
          </motion.div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
