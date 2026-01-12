"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function NavItem({ href, label }: { href: string; label: string }) {
    const pathname = usePathname();
    const active = pathname === href || pathname.startsWith(`${href}/`);

    return (
        <Link href={href} className={`block rounded px-3 py-2 text-sm transition-colors ${active ? "bg-zinc-800 text-zinc-50" : "text-zinc-300 hover:bg-zinc-900 hover:text-zinc-50"}`}>
            {label}
        </Link>
    );
}

export function Sidebar() {
    return (
        <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
            <div className="flex items-center gap-3 border-b border-zinc-800 px-4 py-4">
                <div className="h-9 w-9 rounded bg-zinc-800" />
                <div>
                    <div className="text-sm font-semibold leading-4">Xray Panel</div>
                    <div className="text-xs text-zinc-400">управление</div>
                </div>
            </div>

            <nav className="flex-1 p-3">
                <div className="space-y-1">
                    <NavItem href="/nodes" label="Ноды" />
                    <NavItem href="/connections" label="Подключения" />
                </div>
            </nav>

            <div className="border-t border-zinc-800 p-4 text-xs text-zinc-500">API через /api → backend</div>
        </aside>
    );
}
