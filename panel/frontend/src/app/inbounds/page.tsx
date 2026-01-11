"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Inbound, Node } from "@/lib/types";
import { Button, Card, ErrorBox, Input, Select } from "@/components/ui";

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

type InboundUpdate = Partial<Omit<InboundCreate, "node_id">>;

export default function InboundsPage() {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [inbounds, setInbounds] = useState<Inbound[]>([]);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string>("");

    const [filterNodeId, setFilterNodeId] = useState<string>("");

    const [nodeId, setNodeId] = useState<string>("");
    const [name, setName] = useState("");
    const [port, setPort] = useState("443");
    const [protocol, setProtocol] = useState("vless");
    const [network, setNetwork] = useState("tcp");
    const [security, setSecurity] = useState("reality");
    const [sni, setSni] = useState("");
    const [realityDest, setRealityDest] = useState("");
    const [fp, setFp] = useState("chrome");

    const [selectedId, setSelectedId] = useState<number | null>(null);
    const selected = useMemo(() => inbounds.find((x) => x.id === selectedId) ?? null, [inbounds, selectedId]);

    const [editName, setEditName] = useState("");
    const [editPort, setEditPort] = useState("443");
    const [editProtocol, setEditProtocol] = useState("vless");
    const [editNetwork, setEditNetwork] = useState("tcp");
    const [editSecurity, setEditSecurity] = useState("reality");
    const [editSni, setEditSni] = useState("");
    const [editRealityDest, setEditRealityDest] = useState("");
    const [editFp, setEditFp] = useState("chrome");

    async function refresh() {
        setLoading(true);
        setErr("");
        try {
            const [ns, ibs] = await Promise.all([apiFetch<Node[]>("/nodes"), apiFetch<Inbound[]>(filterNodeId ? `/inbounds?node_id=${encodeURIComponent(filterNodeId)}` : "/inbounds")]);
            setNodes(ns);
            setInbounds(ibs);
            if (selectedId && !ibs.some((x) => x.id === selectedId)) setSelectedId(null);
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
    }, [filterNodeId]);

    useEffect(() => {
        if (!selected) return;
        setEditName(selected.name);
        setEditPort(String(selected.port));
        setEditProtocol(selected.protocol);
        setEditNetwork(selected.network);
        setEditSecurity(selected.security);
        setEditSni(selected.sni);
        setEditRealityDest(selected.reality_dest);
        setEditFp(selected.reality_fingerprint);
    }, [selected]);

    async function createInbound() {
        setErr("");
        setLoading(true);
        try {
            const payload: InboundCreate = {
                node_id: Number(nodeId),
                name,
                port: Number(port),
                protocol,
                network,
                security,
                sni,
                reality_dest: realityDest ? realityDest : null,
                reality_fingerprint: fp,
            };
            await apiFetch<Inbound>("/inbounds", { method: "POST", body: payload });
            setName("");
            setSni("");
            setRealityDest("");
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function saveInbound() {
        if (!selected) return;
        setErr("");
        setLoading(true);
        try {
            const payload: InboundUpdate = {
                name: editName,
                port: Number(editPort),
                protocol: editProtocol,
                network: editNetwork,
                security: editSecurity,
                sni: editSni,
                reality_dest: editRealityDest,
                reality_fingerprint: editFp,
            };
            await apiFetch<Inbound>(`/inbounds/${selected.id}`, { method: "PUT", body: payload });
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function deleteInbound() {
        if (!selected) return;
        if (!confirm(`Удалить inbound #${selected.id} (${selected.name})?`)) return;
        setErr("");
        setLoading(true);
        try {
            await apiFetch<{ status: string }>(`/inbounds/${selected.id}`, { method: "DELETE" });
            setSelectedId(null);
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold">Inbounds</h1>
                <div className="flex items-center gap-2">
                    <Select value={filterNodeId} onChange={setFilterNodeId}>
                        <option value="">Все ноды</option>
                        {nodes.map((n) => (
                            <option key={n.id} value={String(n.id)}>
                                #{n.id} {n.name}
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
                        {inbounds.map((ib) => (
                            <button key={ib.id} className={`w-full rounded border px-3 py-2 text-left text-sm transition-colors ${selectedId === ib.id ? "border-zinc-200 bg-zinc-900" : "border-zinc-800 hover:bg-zinc-900/50"}`} onClick={() => setSelectedId(ib.id)}>
                                <div className="font-medium">
                                    #{ib.id} {ib.name}
                                </div>
                                <div className="text-xs text-zinc-400">
                                    node #{ib.node_id} | {ib.protocol}/{ib.security} | {ib.sni} | port {ib.port}
                                </div>
                            </button>
                        ))}
                        {!inbounds.length ? <div className="text-sm text-zinc-500">Inbounds пока нет</div> : null}
                    </div>
                </Card>

                <Card title="Добавить inbound">
                    <div className="space-y-3">
                        <Select value={nodeId} onChange={setNodeId}>
                            <option value="">Выбери ноду</option>
                            {nodes.map((n) => (
                                <option key={n.id} value={String(n.id)}>
                                    #{n.id} {n.name}
                                </option>
                            ))}
                        </Select>
                        <Input value={name} onChange={setName} placeholder="name" />
                        <Input value={port} onChange={setPort} placeholder="port" />
                        <Select value={protocol} onChange={setProtocol}>
                            <option value="vless">vless</option>
                        </Select>
                        <Select value={network} onChange={setNetwork}>
                            <option value="tcp">tcp</option>
                        </Select>
                        <Select value={security} onChange={setSecurity}>
                            <option value="reality">reality</option>
                            <option value="none">none</option>
                        </Select>
                        <Input value={sni} onChange={setSni} placeholder="sni (например vk.com)" />
                        <Input value={realityDest} onChange={setRealityDest} placeholder="reality_dest (опционально)" />
                        <Input value={fp} onChange={setFp} placeholder="fingerprint" />
                        <Button onClick={createInbound} disabled={loading || !nodeId || !name || !port || !protocol || !network || !security || !sni}>
                            Создать
                        </Button>
                    </div>
                </Card>

                <Card
                    title="Детали / Редактирование"
                    right={
                        <Button variant="danger" onClick={deleteInbound} disabled={loading || !selected}>
                            Delete
                        </Button>
                    }
                >
                    {selected ? (
                        <div className="space-y-3">
                            <div className="text-sm text-zinc-400">
                                Inbound #{selected.id} (node #{selected.node_id})
                            </div>
                            <Input value={editName} onChange={setEditName} placeholder="name" />
                            <Input value={editPort} onChange={setEditPort} placeholder="port" />
                            <Input value={editProtocol} onChange={setEditProtocol} placeholder="protocol" />
                            <Input value={editNetwork} onChange={setEditNetwork} placeholder="network" />
                            <Input value={editSecurity} onChange={setEditSecurity} placeholder="security" />
                            <Input value={editSni} onChange={setEditSni} placeholder="sni" />
                            <Input value={editRealityDest} onChange={setEditRealityDest} placeholder="reality_dest" />
                            <Input value={editFp} onChange={setEditFp} placeholder="fingerprint" />
                            <Button onClick={saveInbound} disabled={loading || !editName || !editPort || !editSni}>
                                Сохранить
                            </Button>

                            <div className="rounded border border-zinc-800 bg-zinc-950 p-3 text-xs text-zinc-300">
                                <div>public_key: {selected.reality_public_key}</div>
                                <div>short_id: {selected.reality_short_id}</div>
                                <div>dest: {selected.reality_dest}</div>
                            </div>
                        </div>
                    ) : (
                        <div className="text-sm text-zinc-500">Выбери inbound слева</div>
                    )}
                </Card>
            </div>
        </div>
    );
}
