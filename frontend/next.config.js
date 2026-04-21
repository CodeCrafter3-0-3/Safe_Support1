const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  customWorkerDir: 'worker', // Tells next-pwa to look for our custom Background Sync logic here
  disable: process.env.NODE_ENV === 'development',
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
};

module.exports = withPWA(nextConfig);