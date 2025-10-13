/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    SCANNER_API_URL: process.env.SCANNER_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
