import type { NextConfig } from "next";

const isGitHubPages =
  process.env.GITHUB_PAGES === "true";

const basePath = isGitHubPages
  ? "/Libya_Tourist_Atlas"
  : "";

const nextConfig: NextConfig = {
  output: "export",

  basePath,

  images: {
    unoptimized: true,
  },

  env: {
    NEXT_PUBLIC_BASE_PATH: basePath,
  },

  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
