"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Client, Inbound, Node } from "@/lib/types";
import { Button, Card, ErrorBox, Input, Select } from "@/components/ui";

type ClientUriResp = { uri: string };

type InboundCreate = {
    node_id: number;
    name: string;
    port: number;
    protocol: string;
    network: string;
    security: string;
    sni: string;
    reality_dest?: string | null;
    reality_fingerprint?: string;
};

type ClientCreate = {
    inbound_id: number;
    username: string;
};

export default function ConnectionsPage() {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [inbounds, setInbounds] = useState<Inbound[]>([]);
    const [clients, setClients] = useState<Client[]>([]);

    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string>("");

    const [uriLoadingKey, setUriLoadingKey] = useState<string>("");
    const [clientUriById, setClientUriById] = useState<Record<number, string>>({});

    const [newInboundByNode, setNewInboundByNode] = useState<
        Record<
            number,
            {
                name: string;
                port: string;
                protocol: string;
                network: string;
                security: string;
                sni: string;
                realityDest: string;
                fp: string;
            }
        >
    >({});

    const [newClientByInbound, setNewClientByInbound] = useState<Record<number, string>>({});

    async function refresh() {
        setLoading(true);
        setErr("");
        try {
            const [ns, ibs, cls] = await Promise.all([apiFetch<Node[]>("/nodes"), apiFetch<Inbound[]>("/inbounds"), apiFetch<Client[]>("/clients")]);
            setNodes(ns);
            setInbounds(ibs);
            setClients(cls);
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

    const inboundsByNode = useMemo(() => {
        const m = new Map<number, Inbound[]>();
        for (const ib of inbounds) {
            const arr = m.get(ib.node_id) ?? [];
            arr.push(ib);
            m.set(ib.node_id, arr);
        }
        for (const [, arr] of m) arr.sort((a, b) => a.id - b.id);
        return m;
    }, [inbounds]);

    const clientsByInbound = useMemo(() => {
        const m = new Map<number, Client[]>();
        for (const c of clients) {
            const arr = m.get(c.inbound_id) ?? [];
            arr.push(c);
            m.set(c.inbound_id, arr);
        }
        for (const [, arr] of m) arr.sort((a, b) => a.id - b.id);
        return m;
    }, [clients]);

    function getInboundDraft(nodeId: number) {
        return (
            newInboundByNode[nodeId] || {
                name: "",
                port: "443",
                protocol: "vless",
                network: "tcp",
                security: "reality",
                sni: "",
                realityDest: "",
                fp: "chrome",
            }
        );
    }

    function setInboundDraft(nodeId: number, patch: Partial<ReturnType<typeof getInboundDraft>>) {
        setNewInboundByNode((prev) => ({
            ...prev,
            [nodeId]: {
                ...getInboundDraft(nodeId),
                ...patch,
            },
        }));
    }

    async function createInbound(nodeId: number) {
        const d = getInboundDraft(nodeId);
        setErr("");
        setLoading(true);
        try {
            const payload: InboundCreate = {
                node_id: nodeId,
                name: d.name.trim(),
                port: Number(d.port),
                protocol: d.protocol,
                network: d.network,
                security: d.security,
                sni: d.sni.trim(),
                reality_dest: d.realityDest.trim() ? d.realityDest.trim() : null,
                reality_fingerprint: d.fp || "chrome",
            };
            await apiFetch<Inbound>("/inbounds", { method: "POST", body: payload });
            setInboundDraft(nodeId, { name: "", sni: "", realityDest: "" });
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function createClient(inboundId: number) {
        const username = (newClientByInbound[inboundId] || "").trim();
        if (!username) return;
        setErr("");
        setLoading(true);
        try {
            const payload: ClientCreate = { inbound_id: inboundId, username };
            await apiFetch<Client>("/clients", { method: "POST", body: payload });
            setNewClientByInbound((prev) => ({ ...prev, [inboundId]: "" }));
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function loadUri(clientId: number) {
        setErr("");
        setUriLoadingKey(`c:${clientId}`);
        try {
            const resp = await apiFetch<ClientUriResp>(`/clients/${clientId}/vless-uri`);
            setClientUriById((prev) => ({ ...prev, [clientId]: resp.uri }));
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setUriLoadingKey("");
        }
    }

    async function copyUri(clientId: number) {
        const uri = clientUriById[clientId];
        if (!uri) return;
        try {
            await navigator.clipboard.writeText(uri);
        } catch {
            // ignore
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold">Подключения</h1>
                <Button variant="ghost" onClick={refresh} disabled={loading}>
                    Обновить
                </Button>
            </div>

            {err ? <ErrorBox message={err} /> : null}

            <Card title="Ноды → Inbounds → Клиенты">
                <div className="space-y-3">
                    {!nodes.length ? <div className="text-sm text-zinc-500">Нод пока нет</div> : null}

                    {nodes.map((n) => {
                        const ibs = inboundsByNode.get(n.id) ?? [];
                        const d = getInboundDraft(n.id);

                        return (
                            <details key={n.id} className="rounded border border-zinc-800 bg-zinc-950/40">
                                <summary className="cursor-pointer select-none px-4 py-3">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-sm text-zinc-400">Нода</div>
                                            <div className="font-medium">{n.name}</div>
                                            <div className="mt-1 break-all text-xs text-zinc-500">{n.url}</div>
                                        </div>
                                        <div className="text-xs text-zinc-400">inbounds: {ibs.length}</div>
                                    </div>
                                </summary>

                                <div className="border-t border-zinc-800 p-4">
                                    <div className="mb-4 rounded border border-zinc-800 bg-zinc-950 p-3">
                                        <div className="mb-2 text-sm font-medium">Добавить inbound</div>
                                        <div className="grid gap-2 md:grid-cols-4">
                                            <Input value={d.name} onChange={(v) => setInboundDraft(n.id, { name: v })} placeholder="name" />
                                            <Input value={d.sni} onChange={(v) => setInboundDraft(n.id, { sni: v })} placeholder="sni (vk.com)" />
                                            <Input value={d.port} onChange={(v) => setInboundDraft(n.id, { port: v })} placeholder="port" />
                                            <Input value={d.realityDest} onChange={(v) => setInboundDraft(n.id, { realityDest: v })} placeholder="dest (опц)" />
                                        </div>
                                        <div className="mt-2 grid gap-2 md:grid-cols-4">
                                            <Select value={d.protocol} onChange={(v) => setInboundDraft(n.id, { protocol: v })}>
                                                <option value="vless">vless</option>
                                            </Select>
                                            <Select value={d.network} onChange={(v) => setInboundDraft(n.id, { network: v })}>
                                                <option value="tcp">tcp</option>
                                            </Select>
                                            <Select value={d.security} onChange={(v) => setInboundDraft(n.id, { security: v })}>
                                                <option value="reality">reality</option>
                                                <option value="none">none</option>
                                            </Select>
                                            <Input value={d.fp} onChange={(v) => setInboundDraft(n.id, { fp: v })} placeholder="fp (chrome)" />
                                        </div>
                                        <div className="mt-2">
                                            <Button onClick={() => createInbound(n.id)} disabled={loading || !d.name.trim() || !d.sni.trim()}>
                                                Создать inbound
                                            </Button>
                                        </div>
                                    </div>

                                    {!ibs.length ? (
                                        <div className="text-sm text-zinc-500">Inbounds пока нет</div>
                                    ) : (
                                        <div className="space-y-3">
                                            {ibs.map((ib) => {
                                                const cls = clientsByInbound.get(ib.id) ?? [];
                                                const newClient = newClientByInbound[ib.id] || "";

                                                return (
                                                    <details key={ib.id} className="rounded border border-zinc-800 bg-zinc-950">
                                                        <summary className="cursor-pointer select-none px-4 py-3">
                                                            <div className="flex items-center justify-between">
                                                                <div>
                                                                    <div className="font-medium">{ib.name}</div>
                                                                    <div className="mt-1 text-xs text-zinc-400">
                                                                        {ib.protocol}/{ib.security} | {ib.sni} | port {ib.port}
                                                                    </div>
                                                                </div>
                                                                <div className="text-xs text-zinc-400">clients: {cls.length}</div>
                                                            </div>
                                                        </summary>

                                                        <div className="border-t border-zinc-800 p-4">
                                                            <div className="mb-3 rounded border border-zinc-800 bg-zinc-950/40 p-3">
                                                                <div className="mb-2 text-sm font-medium">Добавить клиента</div>
                                                                <div className="flex items-center gap-2">
                                                                    <Input value={newClient} onChange={(v) => setNewClientByInbound((prev) => ({ ...prev, [ib.id]: v }))} placeholder="username" />
                                                                    <Button onClick={() => createClient(ib.id)} disabled={loading || !newClient.trim()}>
                                                                        Создать
                                                                    </Button>
                                                                </div>
                                                            </div>

                                                            {!cls.length ? (
                                                                <div className="text-sm text-zinc-500">Клиентов нет</div>
                                                            ) : (
                                                                <div className="overflow-auto rounded border border-zinc-800">
                                                                    <table className="w-full text-left text-sm">
                                                                        <thead className="bg-zinc-900/40 text-xs text-zinc-400">
                                                                            <tr>
                                                                                <th className="px-3 py-2">ID</th>
                                                                                <th className="px-3 py-2">Username</th>
                                                                                <th className="px-3 py-2">UUID</th>
                                                                                <th className="px-3 py-2">URI</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody>
                                                                            {cls.map((c) => {
                                                                                const uri = clientUriById[c.id] || "";
                                                                                const uriLoading = uriLoadingKey === `c:${c.id}`;

                                                                                return (
                                                                                    <tr key={c.id} className="border-t border-zinc-800">
                                                                                        <td className="px-3 py-2 text-zinc-300">{c.id}</td>
                                                                                        <td className="px-3 py-2 text-zinc-100">{c.username}</td>
                                                                                        <td className="px-3 py-2 break-all font-mono text-xs text-zinc-300">{c.uuid}</td>
                                                                                        <td className="px-3 py-2">
                                                                                            <div className="flex items-center gap-2">
                                                                                                <Button variant="ghost" onClick={() => loadUri(c.id)} disabled={uriLoading}>
                                                                                                    {uriLoading ? "..." : "Показать"}
                                                                                                </Button>
                                                                                                <Button variant="ghost" onClick={() => copyUri(c.id)} disabled={!uri}>
                                                                                                    Copy
                                                                                                </Button>
                                                                                            </div>
                                                                                            {uri ? <div className="mt-2 break-all rounded border border-zinc-800 bg-zinc-950 p-2 font-mono text-xs text-zinc-200">{uri}</div> : null}
                                                                                        </td>
                                                                                    </tr>
                                                                                );
                                                                            })}
                                                                        </tbody>
                                                                    </table>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </details>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            </details>
                        );
                    })}
                </div>
            </Card>
        </div>
    );
}
