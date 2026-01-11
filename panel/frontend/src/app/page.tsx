import Link from "next/link";

export default function HomePage() {
    return (
        <div className="space-y-4">
            <h1 className="text-2xl font-semibold">Панель управления</h1>
            <p className="text-zinc-300">UI для FastAPI backend. Тут можно управлять нодами, inbounds и клиентами, а также делать push конфигов.</p>
            <div className="grid gap-3 md:grid-cols-3">
                <Link href="/nodes" className="rounded border border-zinc-800 bg-zinc-900/30 p-4 hover:bg-zinc-900/50">
                    <div className="font-medium">Ноды</div>
                    <div className="text-sm text-zinc-400">Создание / редактирование / push</div>
                </Link>
                <Link href="/inbounds" className="rounded border border-zinc-800 bg-zinc-900/30 p-4 hover:bg-zinc-900/50">
                    <div className="font-medium">Inbounds</div>
                    <div className="text-sm text-zinc-400">Reality / VLESS параметры</div>
                </Link>
                <Link href="/clients" className="rounded border border-zinc-800 bg-zinc-900/30 p-4 hover:bg-zinc-900/50">
                    <div className="font-medium">Clients</div>
                    <div className="text-sm text-zinc-400">UUID / уровень</div>
                </Link>
            </div>
        </div>
    );
}
