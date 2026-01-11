import React from "react";

export function Button({ children, onClick, disabled, variant = "default", type }: { children: React.ReactNode; onClick?: () => void; disabled?: boolean; variant?: "default" | "danger" | "ghost"; type?: "button" | "submit" }) {
    const base = "inline-flex items-center justify-center rounded px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
    const styles = variant === "danger" ? "bg-red-600 hover:bg-red-700 text-white" : variant === "ghost" ? "bg-transparent hover:bg-zinc-900 text-zinc-200 border border-zinc-800" : "bg-zinc-100 hover:bg-white text-zinc-900";

    return (
        <button type={type ?? "button"} className={`${base} ${styles}`} onClick={onClick} disabled={disabled}>
            {children}
        </button>
    );
}

export function Input({ value, onChange, placeholder, type }: { value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
    return <input className="w-full rounded border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} type={type ?? "text"} />;
}

export function Select({ value, onChange, children }: { value: string; onChange: (v: string) => void; children: React.ReactNode }) {
    return (
        <select className="w-full rounded border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100" value={value} onChange={(e) => onChange(e.target.value)}>
            {children}
        </select>
    );
}

export function Card({ title, children, right }: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
    return (
        <div className="rounded border border-zinc-800 bg-zinc-900/30">
            <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
                <div className="font-medium">{title}</div>
                {right}
            </div>
            <div className="p-4">{children}</div>
        </div>
    );
}

export function ErrorBox({ message }: { message: string }) {
    return <div className="rounded border border-red-900 bg-red-950/40 p-3 text-sm text-red-200">{message}</div>;
}
