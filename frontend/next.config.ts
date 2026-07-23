import type { NextConfig } from 'next';

const publicApiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '');
const backendUrl = publicApiUrl || 'http://localhost:5000';
const isStaticExport = process.env.STATIC_EXPORT === 'true';

const nextConfig: NextConfig = {
  output: isStaticExport ? 'export' : 'standalone',
  trailingSlash: isStaticExport,
  images: {
    unoptimized: isStaticExport,
  },
  ...(!isStaticExport && {
    async rewrites() {
      if (publicApiUrl) {
        return [];
      }
      return [
        {
          source: '/api/:path*',
          destination: `${backendUrl}/api/:path*`,
        },
      ];
    },
  }),
};

export default nextConfig;
