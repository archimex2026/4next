import { NextRequest, NextResponse } from 'next/server';

export function proxy(request: NextRequest) {
  const origin = process.env.BACKEND_ORIGIN;
  if (!origin) return NextResponse.next();
  const destination = new URL(origin);
  destination.pathname = request.nextUrl.pathname;
  destination.search = request.nextUrl.search;
  const headers = new Headers(request.headers);
  // Overwrite any client-supplied value. This secret is an upstream request header only.
  headers.delete('x-4next-proxy-key');
  if (process.env.DEMO_PROXY_TOKEN) headers.set('x-4next-proxy-key', process.env.DEMO_PROXY_TOKEN);
  return NextResponse.rewrite(destination, { request: { headers } });
}

export const config = { matcher: ['/api/:path*', '/media/:path*'] };
