import test from 'node:test';import assert from 'node:assert/strict';import worker from '../dist/server/index.js';
const get=path=>worker.fetch(new Request('https://example.com'+path));
test('product route renders crawlable HTML',async()=>{const r=await get('/catalog/0445120075/');assert.equal(r.status,200);const h=await r.text();assert.match(h,/0445120075/);assert.match(h,/application\/ld\+json/);assert.match(h,/priceCurrency/)});
test('unknown routes return real 404',async()=>assert.equal((await get('/missing/')).status,404));
test('canonical directory redirects preserve queries',async()=>{const r=await get('/catalog?q=bosch');assert.equal(r.status,301);assert.equal(r.headers.get('location'),'https://example.com/catalog/?q=bosch')});
test('private preview robots do not index an unfinished domain',async()=>{const r=await get('/robots.txt');assert.match(await r.text(),/Disallow: \//);assert.match(r.headers.get('x-robots-tag'),/noindex/)});
test('configuration endpoint reports mail unavailable without secrets',async()=>assert.deepEqual(await(await get('/api/config')).json(),{submissionEnabled:false,consentVersion:'2026-10-04'}));

test('explicit error page returns 404',async()=>assert.equal((await get('/404/')).status,404));
test('uppercase product URL canonicalizes in a single hop',async()=>{const r=await get('/catalog/RE507959/index.html?utm_source=test');assert.equal(r.status,301);assert.equal(r.headers.get('location'),'https://example.com/catalog/re507959/?utm_source=test')});
