import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    const backendHost = process.env.INTERNAL_BACKEND_HOST || "backend";
    return [
      {
        source: "/api/v1/:path*",
        destination: `http://${backendHost}:8000/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
