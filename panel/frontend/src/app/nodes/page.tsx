"use client";

import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import type { Node } from "@/lib/types";
import { Button, Card, ErrorBox, Input } from "@/components/ui";

type NodeCreate = { name: string; url: string; node_key: string };

type NodeUpdate = Partial<NodeCreate>;

type PushResp = {
    status: string;
    node_response: unknown;
};

export default function NodesPage() {
    const [nodes, setNodes] = useState<Node[]>([]);
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string>("");

    const [name, setName] = useState("");
    const [url, setUrl] = useState("");
    const [nodeKey, setNodeKey] = useState("");

    const [selectedId, setSelectedId] = useState<number | null>(null);
    const selected = useMemo(() => nodes.find((n) => n.id === selectedId) ?? null, [nodes, selectedId]);

    const [editName, setEditName] = useState("");
    const [editUrl, setEditUrl] = useState("");
    const [editKey, setEditKey] = useState("");

    const [configJson, setConfigJson] = useState<string>("");
    const [pushResult, setPushResult] = useState<string>("");

    async function refresh() {
        setLoading(true);
        setErr("");
        try {
            const data = await apiFetch<Node[]>("/nodes");
            setNodes(data);
            if (selectedId && !data.some((n) => n.id === selectedId)) {
                setSelectedId(null);
            }
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
        if (!selected) return;
        setEditName(selected.name);
        setEditUrl(selected.url);
        setEditKey("");
        setConfigJson("");
        setPushResult("");
    }, [selected]);

    async function createNode() {
        setErr("");
        setLoading(true);
        try {
            const payload: NodeCreate = { name, url, node_key: nodeKey };
            await apiFetch<Node>("/nodes", { method: "POST", body: payload });
            setName("");
            setUrl("");
            setNodeKey("");
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function saveNode() {
        if (!selected) return;
        setErr("");
        setLoading(true);
        try {
            const payload: NodeUpdate = {
                name: editName,
                url: editUrl,
            };
            if (editKey.trim()) payload.node_key = editKey.trim();

            await apiFetch<Node>(`/nodes/${selected.id}`, {
                method: "PUT",
                body: payload,
            });
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function deleteNode() {
        if (!selected) return;
        if (!confirm(`Удалить ноду #${selected.id} (${selected.name})?`)) return;
        setErr("");
        setLoading(true);
        try {
            await apiFetch<{ status: string }>(`/nodes/${selected.id}`, {
                method: "DELETE",
            });
            setSelectedId(null);
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function loadConfig() {
        if (!selected) return;
        setErr("");
        setLoading(true);
        try {
            const cfg = await apiFetch<unknown>(`/nodes/${selected.id}/config`);
            setConfigJson(JSON.stringify(cfg, null, 2));
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    async function pushConfig() {
        if (!selected) return;
        setErr("");
        setLoading(true);
        try {
            const resp = await apiFetch<PushResp>(`/nodes/${selected.id}/push`, {
                method: "POST",
            });
            setPushResult(JSON.stringify(resp, null, 2));
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold">Ноды</h1>
                <Button variant="ghost" onClick={refresh} disabled={loading}>
                    Обновить
                </Button>
            </div>

            {err ? <ErrorBox message={err} /> : null}

            <div className="grid gap-4 md:grid-cols-2">
                <Card title="Список" right={<div className="text-sm text-zinc-400">{loading ? "loading..." : `${nodes.length} шт.`}</div>}>
                    <div className="space-y-2">
                        {nodes.map((n) => (
                            <button key={n.id} className={`w-full rounded border px-3 py-2 text-left text-sm transition-colors ${selectedId === n.id ? "border-zinc-200 bg-zinc-900" : "border-zinc-800 hover:bg-zinc-900/50"}`} onClick={() => setSelectedId(n.id)}>
                                <div className="font-medium">
                                    #{n.id} {n.name}
                                </div>
                                <div className="text-xs text-zinc-400 break-all">{n.url}</div>
                            </button>
                        ))}
                        {!nodes.length ? <div className="text-sm text-zinc-500">Нод пока нет</div> : null}
                    </div>
                </Card>

                <Card title="Добавить ноду">
                    <div className="space-y-3">
                        <Input value={name} onChange={setName} placeholder="name" />
                        <Input value={url} onChange={setUrl} placeholder="url (например http://1.2.3.4:8585)" />
                        <Input value={nodeKey} onChange={setNodeKey} placeholder="node_key" />
                        <Button onClick={createNode} disabled={loading || !name || !url || !nodeKey}>
                            Создать
                        </Button>
                    </div>
                </Card>

                <Card
                    title="Детали / Редактирование"
                    right={
                        <div className="flex items-center gap-2">
                            <Button variant="ghost" onClick={loadConfig} disabled={loading || !selected}>
                                Config
                            </Button>
                            <Button variant="ghost" onClick={pushConfig} disabled={loading || !selected}>
                                Push
                            </Button>
                            <Button variant="danger" onClick={deleteNode} disabled={loading || !selected}>
                                Delete
                            </Button>
                        </div>
                    }
                >
                    {selected ? (
                        <div className="space-y-3">
                            <div className="text-sm text-zinc-400">Нода #{selected.id}</div>
                            <Input value={editName} onChange={setEditName} placeholder="name" />
                            <Input value={editUrl} onChange={setEditUrl} placeholder="url" />
                            <Input value={editKey} onChange={setEditKey} placeholder="node_key (введи, если хочешь заменить)" />
                            <Button onClick={saveNode} disabled={loading || !editName || !editUrl}>
                                Сохранить
                            </Button>

                            {configJson ? <pre className="max-h-80 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-3 text-xs">{configJson}</pre> : null}

                            {pushResult ? <pre className="max-h-60 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-3 text-xs">{pushResult}</pre> : null}
                        </div>
                    ) : (
                        <div className="text-sm text-zinc-500">Выбери ноду слева</div>
                    )}
                </Card>
            </div>
        </div>
    );
}
