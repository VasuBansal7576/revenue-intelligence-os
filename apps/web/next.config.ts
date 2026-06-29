import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1"],
  devIndicators: false,
  outputFileTracingRoot: path.join(process.cwd(), "../.."),
  transpilePackages: [
    "@causal-deal/types"
  ]
};

export default nextConfig;
