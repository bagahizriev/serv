import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";

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
                <div className="flex">
                    <Sidebar />
                    <main className="min-h-screen flex-1 bg-zinc-950">
                        <div className="mx-auto max-w-6xl px-6 py-6">{children}</div>
                    </main>
                </div>
            </body>
        </html>
    );
}
