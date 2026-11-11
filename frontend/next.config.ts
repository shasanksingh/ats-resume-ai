import type { NextConfig } from "next";

const productionBackendUrl = "https://ats-resume-ai-production.up.railway.app";
const publicApiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
const backendUrl =
  process.env.BACKEND_URL ||
  (publicApiBase?.startsWith("http") ? publicApiBase : undefined) ||
  (process.env.NODE_ENV === "production" ? productionBackendUrl : "http://127.0.0.1:8000");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  distDir: process.env.NEXT_DIST_DIR || ".next",
  experimental: {
    cpus: 1,
    // Allow the backend's NVIDIA timeout to return a useful error to the UI.
    proxyTimeout: 150_000
  },
  webpack(config, { dev }) {
    // Some Windows Node installations fail while webpack creates its large
    // development cache buffer. Dev recompilation is small for this app, so
    // avoiding that cache is more reliable and does not affect production.
    if (dev) {
      config.cache = false;
    }
    return config;
  },
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendUrl}/:path*`
      }
    ];
  }
};

export default nextConfig;
