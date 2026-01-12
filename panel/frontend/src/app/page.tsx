import Link from "next/link";

export default function HomePage() {
    return (
        <div className="space-y-4">
            <h1 className="text-2xl font-semibold">Панель</h1>
            <p className="text-zinc-300">Два основных раздела: управление нодами и управление подключениями.</p>
            <div className="grid gap-3 md:grid-cols-2">
                <Link href="/nodes" className="rounded border border-zinc-800 bg-zinc-900/30 p-4 hover:bg-zinc-900/50">
                    <div className="font-medium">Ноды</div>
                    <div className="text-sm text-zinc-400">Карточки нод, push/config</div>
                </Link>
                <Link href="/connections" className="rounded border border-zinc-800 bg-zinc-900/30 p-4 hover:bg-zinc-900/50">
                    <div className="font-medium">Подключения</div>
                    <div className="text-sm text-zinc-400">Нода → inbound → клиенты + VLESS URI</div>
                </Link>
            </div>
        </div>
    );
}
