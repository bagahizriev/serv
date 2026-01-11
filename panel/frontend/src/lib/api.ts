type FetchOpts = {
    method?: string;
    body?: unknown;
};

export async function apiFetch<T>(path: string, opts: FetchOpts = {}): Promise<T> {
    // Use Next.js rewrite: /api/* -> backend
    const res = await fetch(`/api${path}`, {
        method: opts.method ?? "GET",
        headers: {
            "Content-Type": "application/json",
        },
        body: opts.body ? JSON.stringify(opts.body) : undefined,
        cache: "no-store",
    });

    if (!res.ok) {
        const text = await res.text();
        throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }

    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
        return (await res.json()) as T;
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (await res.text()) as any as T;
}
