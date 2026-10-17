import type { NextConfig } from "next";

// Keep sessions and downloads on the website origin when the API is hosted elsewhere.
const backendOrigin = process.env.BACKEND_ORIGIN?.replace(/\/$/, '');
if (backendOrigin) {
  const url = new URL(backendOrigin);
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((url.protocol !== 'https:' && !(local && url.protocol === 'http:')) || url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('BACKEND_ORIGIN must be an HTTPS origin without a path or credentials (HTTP is allowed on loopback only).');
  }
}

const nextConfig: NextConfig = {
  output: 'standalone',
};

export default nextConfig;
