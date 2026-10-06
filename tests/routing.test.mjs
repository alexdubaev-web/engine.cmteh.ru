import test from 'node:test';
import { after } from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { cpSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const fixture = process.env.ROUTING_DIST ? null : path.resolve(mkdtempSync(path.join(tmpdir(), 'engine-routing-')));
if (fixture) after(() => rmSync(fixture, { recursive: true, force: true }));
if (fixture) {
  const copy = path.join(fixture, 'project');
  mkdirSync(copy, { recursive: true });
  for (const item of ['build.py', 'seo.py', 'pipeline_io.py', 'data', 'public', 'docs', 'src', '.openai']) {
    cpSync(path.join(projectRoot, item), path.join(copy, item), { recursive: true });
  }
  mkdirSync(path.join(copy, 'backend'), { recursive: true });
  cpSync(path.join(projectRoot, 'backend', 'catalog.json'), path.join(copy, 'backend', 'catalog.json'));
  writeFileSync(path.join(fixture, 'package.json'), '{"type":"module"}', 'utf8');
  const targets = ['dist/server/index.js', 'data/catalog-built.json', 'data/seo-catalog.json',
    'data/seo-state.json', 'data/seo-changes.json', 'backend/catalog.json'];
  const snapshot = () => targets.map(file => readFileSync(path.join(copy, file)));
  const modes = ['preview', 'production'];
  for (const mode of modes) {
    const env = { ...process.env, INDEXNOW_KEY: '', INDEXABLE: mode === 'production' ? 'true' : 'false',
      PUBLIC_SITE_URL: mode === 'production' ? 'https://engine.cmteh.ru' : '' };
    const built = spawnSync('python', ['build.py'], { cwd: copy, env, encoding: 'utf8' });
    assert.equal(built.status, 0, `controlled ${mode} build failed: ${built.stderr}`);
    if (mode === 'preview') {
      const before = snapshot();
      const catalogPath = path.join(copy, 'data/products.json');
      const original = readFileSync(catalogPath);
      const broken = JSON.parse(original.toString('utf8'));
      broken[0].sku = 'unknown-test-sku';
      writeFileSync(catalogPath, JSON.stringify(broken), 'utf8');
      const failed = spawnSync('python', ['build.py'], { cwd: copy, env, encoding: 'utf8' });
      writeFileSync(catalogPath, original);
      assert.notEqual(failed.status, 0, 'injected invalid product must fail the build');
      assert.deepEqual(snapshot(), before, 'failed build must preserve published output and generated state');
      const lateFailure = spawnSync('python', ['build.py'], { cwd: copy,
        env: { ...env, INDEXNOW_KEY: 'invalid key' }, encoding: 'utf8' });
      assert.notEqual(lateFailure.status, 0, 'invalid IndexNow key must fail after rendering');
      assert.deepEqual(snapshot(), before, 'late build failure must preserve published output and generated state');
    }
    const destination = path.join(fixture, mode);
    mkdirSync(destination, { recursive: true });
    cpSync(path.join(copy, 'dist', 'server', 'index.js'), path.join(destination, 'index.js'));
  }
}
const dist = process.env.ROUTING_DIST ?? path.join(fixture, process.env.ROUTING_MODE === 'production' ? 'production' : 'preview', 'index.js');
const { default: worker } = await import(pathToFileURL(dist).href);
const productionWorker = fixture ? (await import(pathToFileURL(path.join(fixture, 'production', 'index.js')).href)).default : worker;
const production = process.env.ROUTING_MODE === 'production';
const get = path => worker.fetch(new Request('https://example.com' + path));

test('product route renders crawlable HTML', async () => {
  const response = await get('/catalog/0445120075/');
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /0445120075/);
  assert.match(html, /application\/ld\+json/);
  assert.match(html, /priceCurrency/);
});
test('unknown routes return real 404', async () => assert.equal((await get('/missing/')).status, 404));
test('hosting metadata is not exposed by the worker asset bundle', async () =>
  assert.equal((await get('/.openai/hosting.json')).status, 404));
test('canonical directory redirects preserve queries', async () => {
  const response = await get('/catalog?q=bosch');
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://example.com/catalog/?q=bosch');
});
test('robots match the selected preview or production build mode', async () => {
  const response = await get('/robots.txt');
  const body = await response.text();
  if (production) {
    assert.match(body, /Sitemap:/);
    assert.doesNotMatch(body, /Disallow: \/\s*$/);
  } else {
    assert.match(body, /Disallow: \//);
    assert.match(response.headers.get('x-robots-tag'), /noindex/);
  }
});
test('controlled production fixture remains indexable', async () => {
  if (!fixture) return;
  const response = await productionWorker.fetch(new Request('https://example.com/robots.txt'));
  const body = await response.text();
  assert.match(body, /Sitemap:/);
  assert.doesNotMatch(body, /Disallow: \/\s*$/);
});
test('configuration endpoint reports mail unavailable without secrets', async () =>
  assert.deepEqual(await (await get('/api/config')).json(), { submissionEnabled: false, consentVersion: '2026-10-06' }));
test('explicit error page returns 404', async () => assert.equal((await get('/404/')).status, 404));
test('uppercase product URL canonicalizes in a single hop', async () => {
  const response = await get('/catalog/RE507959/index.html?utm_source=test');
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://example.com/catalog/re507959/?utm_source=test');
});
