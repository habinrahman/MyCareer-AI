/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  compress: true,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  async rewrites() {
    return [{ source: "/favicon.ico", destination: "/icon.svg" }];
  },
  async redirects() {
    const main = "/tools/resume-intelligence";
    return [
      { source: "/dashboard", destination: main, permanent: false },
      { source: "/dashboard/:path*", destination: main, permanent: false },
      { source: "/resume", destination: main, permanent: false },
      { source: "/resume/:path*", destination: main, permanent: false },
      { source: "/chat", destination: main, permanent: false },
      { source: "/chat/:path*", destination: main, permanent: false },
      { source: "/reports", destination: main, permanent: false },
      { source: "/reports/:path*", destination: main, permanent: false },
      { source: "/analysis/:path*", destination: main, permanent: false },
      { source: "/careers", destination: main, permanent: false },
      { source: "/careers/:path*", destination: main, permanent: false },
      { source: "/settings", destination: main, permanent: false },
      { source: "/settings/:path*", destination: main, permanent: false },
      { source: "/auth/:path*", destination: main, permanent: false },
    ];
  },
};

export default nextConfig;
