/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // API routes configuration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'development' 
          ? 'http://localhost:8000/api/:path*'
          : '/.netlify/functions/api/:path*'
      },
      {
        source: '/ws/:path*',
        destination: process.env.NODE_ENV === 'development'
          ? 'ws://localhost:8000/ws/:path*'
          : '/.netlify/functions/api/ws/:path*'
      }
    ]
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 
      (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : ''),
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 
      (process.env.NODE_ENV === 'development' ? 'ws://localhost:8000' : '')
  }
}

module.exports = nextConfig