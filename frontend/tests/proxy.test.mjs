import assert from 'node:assert/strict';
import { afterEach, test } from 'node:test';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { runInNewContext } from 'node:vm';
import { Readable } from 'node:stream';
import ts from 'typescript';
import { NextRequest } from 'next/server.js';
import { getCloneableBody } from 'next/dist/server/body-streams.js';

// Exercise the real source with Next's request/response objects, without a build or extra runner.
const compiled = ts.transpileModule(readFileSync(new URL('../src/proxy.ts', import.meta.url), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const exports = {};
runInNewContext(compiled, { exports, require: createRequire(import.meta.url), process, URL, Headers });
const { proxy, config } = exports;
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
  const compiledConfig = ts.transpileModule(readFileSync(new URL('../next.config.ts', import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const configExports = {};
  runInNewContext(compiledConfig, { exports: configExports, process, URL });
  const limit = configExports.default.experimental.proxyClientMaxBodySize;
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
