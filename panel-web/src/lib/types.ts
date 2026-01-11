export type Node = {
    id: number;
    name: string;
    url: string;
};

export type Inbound = {
    id: number;
    node_id: number;
    name: string;
    port: number;
    protocol: string;
    network: string;
    security: string;
    sni: string;
    reality_public_key: string;
    reality_short_id: string;
    reality_dest: string;
    reality_fingerprint: string;
};

export type Client = {
    id: number;
    inbound_id: number;
    username: string;
    uuid: string;
    level: number;
};
