"use client";

import { useEffect, useState } from "react";
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

    const [busyNodeId, setBusyNodeId] = useState<number | null>(null);
    const [configByNode, setConfigByNode] = useState<Record<number, string>>({});
    const [pushByNode, setPushByNode] = useState<Record<number, string>>({});

    const [name, setName] = useState("");
    const [url, setUrl] = useState("");
    const [nodeKey, setNodeKey] = useState("");

    const [editingId, setEditingId] = useState<number | null>(null);
    const [editName, setEditName] = useState("");
    const [editUrl, setEditUrl] = useState("");
    const [editKey, setEditKey] = useState("");

    async function refresh() {
        setLoading(true);
        setErr("");
        try {
            const data = await apiFetch<Node[]>("/nodes");
            setNodes(data);
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

    function startEdit(node: Node) {
        setEditingId(node.id);
        setEditName(node.name);
        setEditUrl(node.url);
        setEditKey("");
    }

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

    async function saveNode(nodeId: number) {
        if (!editingId || editingId !== nodeId) return;
        setErr("");
        setBusyNodeId(nodeId);
        try {
            const payload: NodeUpdate = {
                name: editName,
                url: editUrl,
            };
            if (editKey.trim()) payload.node_key = editKey.trim();

            await apiFetch<Node>(`/nodes/${nodeId}`, {
                method: "PUT",
                body: payload,
            });
            setEditingId(null);
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setBusyNodeId(null);
        }
    }

    async function deleteNode(node: Node) {
        if (!confirm(`Удалить ноду #${node.id} (${node.name})?`)) return;
        setErr("");
        setBusyNodeId(node.id);
        try {
            await apiFetch<{ status: string }>(`/nodes/${node.id}`, {
                method: "DELETE",
            });
            if (editingId === node.id) setEditingId(null);
            await refresh();
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setBusyNodeId(null);
        }
    }

    async function loadConfig(node: Node) {
        setErr("");
        setBusyNodeId(node.id);
        try {
            const cfg = await apiFetch<unknown>(`/nodes/${node.id}/config`);
            setConfigByNode((prev) => ({ ...prev, [node.id]: JSON.stringify(cfg, null, 2) }));
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setBusyNodeId(null);
        }
    }

    async function pushConfig(node: Node) {
        setErr("");
        setBusyNodeId(node.id);
        try {
            const resp = await apiFetch<PushResp>(`/nodes/${node.id}/push`, {
                method: "POST",
            });
            setPushByNode((prev) => ({ ...prev, [node.id]: JSON.stringify(resp, null, 2) }));
        } catch (e) {
            setErr(e instanceof Error ? e.message : String(e));
        } finally {
            setBusyNodeId(null);
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

            <Card title="Добавить ноду">
                <div className="grid gap-3 md:grid-cols-3">
                    <Input value={name} onChange={setName} placeholder="name" />
                    <Input value={url} onChange={setUrl} placeholder="url (например http://1.2.3.4:8585)" />
                    <Input value={nodeKey} onChange={setNodeKey} placeholder="node_key" />
                </div>
                <div className="mt-3">
                    <Button onClick={createNode} disabled={loading || !name || !url || !nodeKey}>
                        Создать
                    </Button>
                </div>
            </Card>

            <div className="grid gap-4 md:grid-cols-2">
                {nodes.map((n) => {
                    const busy = busyNodeId === n.id;
                    const cfg = configByNode[n.id] || "";
                    const push = pushByNode[n.id] || "";
                    const editing = editingId === n.id;

                    return (
                        <div key={n.id} className="rounded border border-zinc-800 bg-zinc-900/30">
                            <div className="flex items-start justify-between border-b border-zinc-800 px-4 py-3">
                                <div>
                                    <div className="text-sm text-zinc-400">Нода #{n.id}</div>
                                    <div className="text-base font-semibold">{n.name}</div>
                                    <div className="mt-1 break-all text-xs text-zinc-400">{n.url}</div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="ghost" onClick={() => loadConfig(n)} disabled={busy}>
                                        Config
                                    </Button>
                                    <Button variant="ghost" onClick={() => pushConfig(n)} disabled={busy}>
                                        Push
                                    </Button>
                                </div>
                            </div>

                            <div className="p-4">
                                <div className="flex items-center gap-2">
                                    {editing ? (
                                        <>
                                            <Button onClick={() => saveNode(n.id)} disabled={busy || !editName || !editUrl}>
                                                Сохранить
                                            </Button>
                                            <Button variant="ghost" onClick={() => setEditingId(null)} disabled={busy}>
                                                Отмена
                                            </Button>
                                        </>
                                    ) : (
                                        <>
                                            <Button variant="ghost" onClick={() => startEdit(n)} disabled={busy}>
                                                Редактировать
                                            </Button>
                                            <Button variant="danger" onClick={() => deleteNode(n)} disabled={busy}>
                                                Delete
                                            </Button>
                                        </>
                                    )}
                                </div>

                                {editing ? (
                                    <div className="mt-3 space-y-3">
                                        <Input value={editName} onChange={setEditName} placeholder="name" />
                                        <Input value={editUrl} onChange={setEditUrl} placeholder="url" />
                                        <Input value={editKey} onChange={setEditKey} placeholder="node_key (если нужно заменить)" />
                                    </div>
                                ) : null}

                                {cfg ? (
                                    <details className="mt-4">
                                        <summary className="cursor-pointer text-sm text-zinc-300">Конфиг</summary>
                                        <pre className="mt-2 max-h-80 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-3 text-xs">{cfg}</pre>
                                    </details>
                                ) : null}

                                {push ? (
                                    <details className="mt-3">
                                        <summary className="cursor-pointer text-sm text-zinc-300">Результат push</summary>
                                        <pre className="mt-2 max-h-60 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-3 text-xs">{push}</pre>
                                    </details>
                                ) : null}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
