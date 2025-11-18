/** @type {import('next').NextConfig} */

const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
      ignored: [
        '**/node_modules/**',
        '**/.next/**',
        '**/.git/**',
        '**/dist/**',
        '**/build/**',
      ],
    }
    return config
  },
  async rewrites() {
    const origin = process.env.BACKEND_ORIGIN || 'http://localhost:8000'

    return {
      beforeFiles: [],
      afterFiles: [
        {
          source: '/api/:path*',
          destination: `${origin}/api/v1/:path*`,
        },
      ],
      fallback: [],
    }
  },
}

module.exports = nextConfig
