/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    async rewrites() {
        // Browser talks to Next.js container. Next.js talks to backend over docker network.
        return [
            {
                source: "/api/:path*",
                destination: process.env.PANEL_API_INTERNAL_URL ? `${process.env.PANEL_API_INTERNAL_URL}/:path*` : "http://backend:8000/:path*",
            },
        ];
    },
};

module.exports = nextConfig;
