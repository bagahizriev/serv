"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Client, Inbound } from "@/lib/types";
import { Button, Card, ErrorBox, Input, Select } from "@/components/ui";

type ClientCreate = {
    inbound_id: number;
    username: string;
};

type ClientUpdate = {
    username?: string;
    level?: number;
};

export default function ClientsPage() {
    const [inbounds, setInbounds] = useState<Inbound[]>([]);
    const [clients, setClients] = useState<Client[]>([]);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string>("");

    const [filterInboundId, setFilterInboundId] = useState<string>("");

    const [inboundId, setInboundId] = useState<string>("");
    const [username, setUsername] = useState("");

    const [selectedId, setSelectedId] = useState<number | null>(null);
    const selected = useMemo(() => clients.find((c) => c.id === selectedId) ?? null, [clients, selectedId]);

    const [editUsername, setEditUsername] = useState("");
    const [editLevel, setEditLevel] = useState("0");

    async function refresh() {
        setLoading(true);
        setErr("");
        try {
            const [ibs, cls] = await Promise.all([apiFetch<Inbound[]>("/inbounds"), apiFetch<Client[]>(filterInboundId ? `/clients?inbound_id=${encodeURIComponent(filterInboundId)}` : "/clients")]);
            setInbounds(ibs);
            setClients(cls);
            if (selectedId && !cls.some((c) => c.id === selectedId)) setSelectedId(null);
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        refresh();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        refresh();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filterInboundId]);

    useEffect(() => {
        if (!selected) return;
        setEditUsername(selected.username);
        setEditLevel(String(selected.level));
    }, [selected]);

    async function createClient() {
        setErr("");
        setLoading(true);
        try {
            const payload: ClientCreate = { inbound_id: Number(inboundId), username };
            await apiFetch<Client>("/clients", { method: "POST", body: payload });
            setUsername("");
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function saveClient() {
        if (!selected) return;
        setErr("");
        setLoading(true);
        try {
            const payload: ClientUpdate = {
                username: editUsername,
                level: Number(editLevel),
            };
            await apiFetch<Client>(`/clients/${selected.id}`, { method: "PUT", body: payload });
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function deleteClient() {
        if (!selected) return;
        if (!confirm(`Удалить client #${selected.id} (${selected.username})?`)) return;
        setErr("");
        setLoading(true);
        try {
            await apiFetch<{ status: string }>(`/clients/${selected.id}`, { method: "DELETE" });
            setSelectedId(null);
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    function inboundLabel(id: number): string {
        const ib = inbounds.find((x) => x.id === id);
        if (!ib) return `inbound #${id}`;
        return `#${ib.id} ${ib.name} (node #${ib.node_id})`;
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold">Clients</h1>
                <div className="flex items-center gap-2">
                    <Select value={filterInboundId} onChange={setFilterInboundId}>
                        <option value="">Все inbounds</option>
                        {inbounds.map((ib) => (
                            <option key={ib.id} value={String(ib.id)}>
                                #{ib.id} {ib.name}
                            </option>
                        ))}
                    </Select>
                    <Button variant="ghost" onClick={refresh} disabled={loading}>
                        Обновить
                    </Button>
                </div>
            </div>

            {err ? <ErrorBox message={err} /> : null}

            <div className="grid gap-4 md:grid-cols-2">
                <Card title="Список">
                    <div className="space-y-2">
                        {clients.map((c) => (
                            <button key={c.id} className={`w-full rounded border px-3 py-2 text-left text-sm transition-colors ${selectedId === c.id ? "border-zinc-200 bg-zinc-900" : "border-zinc-800 hover:bg-zinc-900/50"}`} onClick={() => setSelectedId(c.id)}>
                                <div className="font-medium">
                                    #{c.id} {c.username}
                                </div>
                                <div className="text-xs text-zinc-400 break-all">{c.uuid}</div>
                                <div className="text-xs text-zinc-500">{inboundLabel(c.inbound_id)}</div>
                            </button>
                        ))}
                        {!clients.length ? <div className="text-sm text-zinc-500">Clients пока нет</div> : null}
                    </div>
                </Card>

                <Card title="Добавить клиента">
                    <div className="space-y-3">
                        <Select value={inboundId} onChange={setInboundId}>
                            <option value="">Выбери inbound</option>
                            {inbounds.map((ib) => (
                                <option key={ib.id} value={String(ib.id)}>
                                    #{ib.id} {ib.name} (node #{ib.node_id})
                                </option>
                            ))}
                        </Select>
                        <Input value={username} onChange={setUsername} placeholder="username" />
                        <Button onClick={createClient} disabled={loading || !inboundId || !username}>
                            Создать
                        </Button>
                    </div>
                </Card>

                <Card
                    title="Детали / Редактирование"
                    right={
                        <Button variant="danger" onClick={deleteClient} disabled={loading || !selected}>
                            Delete
                        </Button>
                    }
                >
                    {selected ? (
                        <div className="space-y-3">
                            <div className="text-sm text-zinc-400">Client #{selected.id}</div>
                            <div className="rounded border border-zinc-800 bg-zinc-950 p-3 text-xs break-all">{selected.uuid}</div>
                            <Input value={editUsername} onChange={setEditUsername} placeholder="username" />
                            <Input value={editLevel} onChange={setEditLevel} placeholder="level" />
                            <Button onClick={saveClient} disabled={loading || !editUsername}>
                                Сохранить
                            </Button>
                        </div>
                    ) : (
                        <div className="text-sm text-zinc-500">Выбери клиента слева</div>
                    )}
                </Card>
            </div>
        </div>
    );
}
