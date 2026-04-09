"use client";

import { motion, useScroll, useMotionValueEvent } from "framer-motion";
import { useState, useEffect } from "react";
import { isAuthenticated, getStoredUser, logout } from "@/lib/auth";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";

interface NavbarProps {
    onInquireClick?: () => void;
}

const NAV_LINKS = [
    { href: "/evaluations", label: "Evaluations" },
    { href: "/pipeline", label: "Pipeline" },
    { href: "/admin", label: "Admin" },
];

export default function Navbar({ onInquireClick }: NavbarProps) {
    const { scrollY } = useScroll();
    const [hidden, setHidden] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const pathname = usePathname();
    const [authState, setAuthState] = useState<{
        authenticated: boolean;
        username: string | null;
        role: string | null;
    }>({ authenticated: false, username: null, role: null });
    const [health, setHealth] = useState<{ api: boolean; faiss: boolean; db: boolean }>({
        api: false,
        faiss: false,
        db: false,
    });
    const router = useRouter();

    // Check auth state on mount and periodically
    useEffect(() => {
        const checkAuth = () => {
            const authed = isAuthenticated();
            const user = getStoredUser();
            setAuthState({
                authenticated: authed,
                username: user?.username || null,
                role: user?.role || null,
            });
        };

        checkAuth();
        window.addEventListener("storage", checkAuth);
        const interval = setInterval(checkAuth, 2000);

        return () => {
            window.removeEventListener("storage", checkAuth);
            clearInterval(interval);
        };
    }, []);

    // Health polling every 30s
    useEffect(() => {
        const checkHealth = async () => {
            try {
                const res = await fetch(
                    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/health`,
                    { signal: AbortSignal.timeout(5000) }
                );
                if (res.ok) {
                    const data = await res.json();
                    setHealth({
                        api: true,
                        faiss: data.faiss_loaded ?? data.index_loaded ?? true,
                        db: data.db_connected ?? true,
                    });
                } else {
                    setHealth({ api: false, faiss: false, db: false });
                }
            } catch {
                setHealth({ api: false, faiss: false, db: false });
            }
        };
        checkHealth();
        const interval = setInterval(checkHealth, 30000);
        return () => clearInterval(interval);
    }, []);

    useMotionValueEvent(scrollY, "change", (latest) => {
        const previous = scrollY.getPrevious() ?? 0;
        if (latest > previous && latest > 150) {
            setHidden(true);
        } else {
            setHidden(false);
        }
        setScrolled(latest > 50);
    });

    const handleLogout = () => {
        logout();
        setAuthState({ authenticated: false, username: null, role: null });
        router.refresh();
    };

    const prefersReducedMotion =
        typeof window !== "undefined"
            ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
            : false;

    return (
        <motion.nav
            variants={{
                visible: { y: 0 },
                hidden: { y: "-100%" },
            }}
            animate={hidden ? "hidden" : "visible"}
            transition={{ duration: 0.35, ease: "easeInOut" }}
            className={`fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-8 py-5 transition-colors duration-500 ${scrolled
                ? "bg-pagani-black/80 backdrop-blur-md border-b border-white/10"
                : "bg-transparent"
                }`}
        >
            {/* Logo */}
            <Link href="/" className="text-2xl font-bold tracking-tighter uppercase text-white">
                Pagani <span className="text-pagani-gold">Zonda R</span>
            </Link>

            {/* Center Nav Links */}
            <div className="hidden md:flex items-center gap-1">
                {NAV_LINKS.map((link) => (
                    <Link
                        key={link.href}
                        href={link.href}
                        className={`text-[10px] font-bold tracking-[0.15em] uppercase px-3 py-1.5 rounded transition-all ${pathname === link.href
                                ? "text-pagani-gold border-b-2 border-pagani-gold"
                                : "text-white/50 hover:text-white/80"
                            }`}
                    >
                        {link.label}
                    </Link>
                ))}
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-4">
                {/* Health Status Dots */}
                <div className="hidden md:flex items-center gap-2">
                    {(["api", "faiss", "db"] as const).map((key) => (
                        <div key={key} className="flex items-center gap-1" title={`${key.toUpperCase()}: ${health[key] ? "OK" : "Down"}`}>
                            <div
                                className={`w-2 h-2 rounded-full ${health[key] ? "bg-green-500" : "bg-red-500"
                                    } ${health[key] && !prefersReducedMotion ? "animate-pulse" : ""}`}
                            />
                            <span className="text-[8px] uppercase tracking-wider text-white/30">
                                {key}
                            </span>
                        </div>
                    ))}
                </div>

                {/* User Info */}
                {authState.authenticated && authState.username && (
                    <div className="hidden md:flex items-center gap-2">
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider">
                            {authState.role}
                        </span>
                        <span className="text-xs text-white/70">
                            {authState.username}
                        </span>
                    </div>
                )}

                {/* INQUIRE Button */}
                <button
                    onClick={onInquireClick}
                    className="text-xs font-bold tracking-[0.2em] uppercase text-pagani-gold border border-pagani-gold/30 px-6 py-2 hover:bg-pagani-gold hover:text-black transition-all"
                    style={{ fontFamily: "var(--font-orbitron)" }}
                >
                    Inquire
                </button>

                {/* Auth Button */}
                {authState.authenticated ? (
                    <button
                        onClick={handleLogout}
                        className="hidden md:block text-xs font-bold tracking-[0.15em] uppercase text-gray-400 border border-white/10 px-5 py-2 hover:bg-white/10 hover:text-white transition-all"
                    >
                        Logout
                    </button>
                ) : (
                    <a
                        href="/register"
                        className="hidden md:block text-xs font-bold tracking-[0.15em] uppercase text-white border border-white/20 px-5 py-2 hover:bg-white hover:text-black transition-all"
                    >
                        Sign Up
                    </a>
                )}
            </div>
        </motion.nav>
    );
}
