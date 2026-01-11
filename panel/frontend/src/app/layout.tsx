import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Xray Panel",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="ru">
            <body>
                <div className="min-h-screen">
                    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
                        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded bg-zinc-800" />
                                <div className="font-semibold">Xray Panel</div>
                            </div>
                            <nav className="flex items-center gap-3 text-sm text-zinc-300">
                                <Link className="rounded px-2 py-1 hover:bg-zinc-900" href="/">
                                    Главная
                                </Link>
                                <Link className="rounded px-2 py-1 hover:bg-zinc-900" href="/nodes">
                                    Ноды
                                </Link>
                                <Link className="rounded px-2 py-1 hover:bg-zinc-900" href="/inbounds">
                                    Inbounds
                                </Link>
                                <Link className="rounded px-2 py-1 hover:bg-zinc-900" href="/clients">
                                    Clients
                                </Link>
                            </nav>
                        </div>
                    </header>
                    <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
                </div>
            </body>
        </html>
    );
}
