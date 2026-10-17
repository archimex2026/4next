import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { runInNewContext } from 'node:vm';
import { Readable } from 'node:stream';
import { createServer } from 'node:http';
import ts from 'typescript';
import { NextRequest } from 'next/server.js';
import { getCloneableBody } from 'next/dist/server/body-streams.js';
import { proxyRequest } from 'next/dist/server/lib/router-utils/proxy-request.js';

// Exercise the real source with Next's request/response objects, without a build or extra runner.
const compiled = ts.transpileModule(readFileSync(new URL('../src/proxy.ts', import.meta.url), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const exports = {};
runInNewContext(compiled, { exports, require: createRequire(import.meta.url), process, URL, Headers });
const { proxy, config } = exports;
function nextConfig() {
  const output = ts.transpileModule(readFileSync(new URL('../next.config.ts', import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const result = {};
  runInNewContext(output, { exports: result, process, URL });
  return result.default;
}
const previous = { BACKEND_ORIGIN: process.env.BACKEND_ORIGIN, DEMO_PROXY_TOKEN: process.env.DEMO_PROXY_TOKEN };
afterEach(() => {
  for (const [name, value] of Object.entries(previous)) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
});

test('API/media rewrite preserves URL, session cookie and CSRF origin; replaces forged gateway key', () => {
  process.env.BACKEND_ORIGIN = 'https://api.example.test';
  process.env.DEMO_PROXY_TOKEN = 'server-only-test-token';
  const request = new NextRequest('https://4next.example.test/api/trash?query=a%20b', {
    headers: { cookie: 'session=example', origin: 'https://4next.example.test', 'x-4next-proxy-key': 'forged' },
  });
  const response = proxy(request);
  assert.equal(response.headers.get('x-middleware-rewrite'), 'https://api.example.test/api/trash?query=a%20b');
  assert.equal(response.headers.get('x-middleware-request-cookie'), 'session=example');
  assert.equal(response.headers.get('x-middleware-request-origin'), 'https://4next.example.test');
  assert.equal(response.headers.get('x-middleware-request-x-4next-proxy-key'), 'server-only-test-token');
  // x-middleware-request-* is Next's upstream protocol, never a direct response header.
  assert.equal(response.headers.has('x-4next-proxy-key'), false);
  assert.equal(response.headers.has('set-cookie'), false);
  assert.equal(response.body, null);
  assert.deepEqual(Array.from(config.matcher), ['/api/:path*', '/media/:path*']);
});

test('without a configured gateway token a forged client key is removed', () => {
  process.env.BACKEND_ORIGIN = 'https://api.example.test';
  delete process.env.DEMO_PROXY_TOKEN;
  const response = proxy(new NextRequest('https://4next.example.test/media/audio.mp3', {
    headers: { 'x-4next-proxy-key': 'forged' },
  }));
  assert.equal(response.headers.get('x-middleware-rewrite'), 'https://api.example.test/media/audio.mp3');
  assert.equal(response.headers.has('x-middleware-request-x-4next-proxy-key'), false);
});

test('without an upstream origin the proxy leaves local development routing alone', () => {
  delete process.env.BACKEND_ORIGIN;
  process.env.DEMO_PROXY_TOKEN = 'server-only-test-token';
  const response = proxy(new NextRequest('http://localhost:3000/api/trash'));
  assert.equal(response.headers.get('x-middleware-next'), '1');
  assert.equal(response.headers.has('x-middleware-rewrite'), false);
  assert.equal(response.headers.has('x-middleware-request-x-4next-proxy-key'), false);
});

test('configured Next proxy buffer preserves a maximum upload and bounds oversized bodies', async () => {
  const limit = nextConfig().experimental.proxyClientMaxBodySize;
  const size = 15 * 1024 * 1024 + 4096; // Full file allowance plus real multipart overhead.
  async function received(total) {
    const input = Readable.from((function* () {
      for (let remaining = total; remaining > 0; remaining -= 64 * 1024) {
        yield Buffer.alloc(Math.min(remaining, 64 * 1024));
      }
    })());
    let bytes = 0;
    for await (const chunk of getCloneableBody(input, limit).cloneBodyStream()) bytes += chunk.length;
    return bytes;
  }
  assert.equal(await received(size), size, 'the documented 15 MiB upload must not be truncated');
  const originalWarn = console.warn;
  let warned = false;
  try {
    console.warn = () => { warned = true; };
    assert.equal(await received(16 * 1024 * 1024 + 1), 16 * 1024 * 1024);
    assert.equal(warned, true);
  } finally {
    console.warn = originalWarn;
  }
});

test('real Next upstream proxy lets analysis finish and still enforces a finite timeout', { timeout: 10_000 }, async t => {
  const configuredTimeout = nextConfig().experimental.proxyTimeout;
  assert.ok(configuredTimeout >= 90_000 && configuredTimeout <= 120_000, 'analysis has a bounded 90–120 second window');
  async function listen(server) {
    await new Promise((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', resolve);
    });
    t.after(() => { server.closeAllConnections(); server.close(); });
    return `http://127.0.0.1:${server.address().port}`;
  }
  const upstream = await listen(createServer((_req, res) => {
    // Scale 45 seconds of model work down by 100; this exceeds the old 30 second default.
    const timer = setTimeout(() => res.end('analysis complete'), 450);
    res.once('close', () => clearTimeout(timer));
  }));
  let timeout = configuredTimeout / 100;
  let proxyErrors = 0;
  const target = new URL(`${upstream}/api/books/upload`);
  const gateway = await listen(createServer((req, res) => {
    void proxyRequest(req, res, { protocol: target.protocol, hostname: target.hostname, port: target.port, pathname: target.pathname, query: {} }, undefined, undefined, timeout)
      .catch(() => { proxyErrors += 1; });
  }));
  const completed = await fetch(gateway, { signal: AbortSignal.timeout(3000) });
  assert.equal(completed.status, 200);
  assert.equal(await completed.text(), 'analysis complete');
  assert.equal(proxyErrors, 0);
  timeout = 20;
  const originalError = console.error;
  try {
    // The installed Next proxy logs the expected timeout before responding with 500.
    console.error = () => {};
    const expired = await fetch(gateway, { signal: AbortSignal.timeout(3000) });
    assert.equal(expired.status, 500);
    assert.equal(await expired.text(), 'Internal Server Error');
    assert.equal(proxyErrors, 1);
  } finally {
    console.error = originalError;
  }
});
