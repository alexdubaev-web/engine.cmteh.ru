import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = (await readFile(new URL('../public/assets/analytics.js', import.meta.url), 'utf8'))
  .replace('export function createAnalyticsConsent', 'function createAnalyticsConsent')
  .replace(/\ntry \{ createAnalyticsConsent\([\s\S]*$/, '\nglobalThis.createAnalyticsConsent = createAnalyticsConsent;');
const context = vm.createContext({ URL, Date, JSON, Number });
vm.runInContext(source, context);
const create = context.createAnalyticsConsent;
const KEY = 'cmteh.analytics-consent.v1';

function fixture({ hostname = 'engine.cmteh.ru', stored = null, storageThrows = false, now = 1_800_000_000_000, sharedValues = null } = {}) {
  const events = { allow: null, deny: null, preferences: null, keydown: null };
  const calls = [];
  const status = { textContent: '' };
  const panel = { hidden: true, querySelector: selector => selector.includes('allow') ? { focus() {}, addEventListener: (_type, fn) => events.allow = fn } : selector.includes('deny') ? { addEventListener: (_type, fn) => events.deny = fn } : status };
  const head = { appendChild(node) { node.parentNode = head; calls.push(node); }, removeChild(node) { node.parentNode = null; } };
  const doc = { referrer: 'https://search.example/find?q=private#frag', hidden: false, addEventListener: (type, fn) => events[type] = fn, head, querySelector: () => panel,
    querySelectorAll: () => [{ addEventListener: (_type, fn) => events.preferences = fn }],
    createElement: () => ({}), };
  const values = sharedValues || new Map(stored ? [[KEY, typeof stored === 'string' ? stored : JSON.stringify(stored)]] : []);
  let writesBlocked = storageThrows, clock = now;
  const storage = { getItem: key => { if (storageThrows) throw Error('blocked'); return values.get(key) ?? null; },
    setItem: (key, value) => { if (writesBlocked) throw Error('blocked'); values.set(key, value); },
    removeItem: key => { if (writesBlocked) throw Error('blocked'); values.delete(key); } };
  const listeners = new Map();
  const win = { location: { hostname, origin: 'https://engine.cmteh.ru', pathname: '/catalog/' },
    addEventListener: (type, fn) => { events[type] = fn; listeners.set(type, [...(listeners.get(type) || []), fn]); },
    dispatch: (type, event) => (listeners.get(type) || []).forEach(fn => fn(event)) };
  return { events, calls, panel, doc, win, storage, values, now, setNow: value => { clock = value; }, blockWrites: () => { writesBlocked = true; }, run: () => create({ window: win, document: doc, storage, now: () => clock }) };
}

test('no counter request before a choice, and refusal persists without loading it', () => {
  const f = fixture(); f.run();
  assert.equal(f.panel.hidden, false); assert.equal(f.calls.length, 0);
  f.events.deny();
  assert.equal(f.calls.length, 0); assert.equal(f.panel.hidden, true);
  assert.equal(JSON.parse(f.values.get(KEY)).decision, 'rejected');
});

test('accept loads the counter only then and initializes configured features with clean URLs', () => {
  const f = fixture(); f.run(); assert.equal(f.calls.length, 0);
  f.events.allow(); assert.equal(f.calls.length, 1);
  const script = f.calls[0];
  assert.equal(script.src, 'https://mc.yandex.ru/metrika/tag.js?id=113475902');
  assert.equal(script.referrerPolicy, 'no-referrer');
  script.onload();
  const init = f.win.ym.a.find(args => args[1] === 'init');
  assert.equal(init[0], 113475902);
  assert.deepEqual({ ssr: init[2].ssr, webvisor: init[2].webvisor, clickmap: init[2].clickmap,
    ecommerce: init[2].ecommerce, accurateTrackBounce: init[2].accurateTrackBounce, trackLinks: init[2].trackLinks },
  { ssr: true, webvisor: true, clickmap: true, ecommerce: 'dataLayer', accurateTrackBounce: true, trackLinks: true });
  assert.equal(init[2].url, 'https://engine.cmteh.ru/catalog/');
  assert.equal(init[2].referrer, 'https://search.example/find');
});

test('expired, malformed, and inaccessible consent records never load analytics', () => {
  for (const stored of [
    { version: 1, decision: 'accepted', savedAt: 1 },
    { version: 8, decision: 'accepted', savedAt: 1_800_000_000_000 },
    '{broken json'
  ]) {
    const f = fixture({ stored }); f.run();
    assert.equal(f.calls.length, 0); assert.equal(f.panel.hidden, false);
  }
  const blocked = fixture({ storageThrows: true }); blocked.run(); blocked.events.allow();
  assert.equal(blocked.calls.length, 0); assert.equal(blocked.panel.hidden, false);
  assert.match(blocked.panel.querySelector('[data-analytics-status]').textContent, /останется выключенной/);
});

test('an in-flight script cannot initialize after refusal; refusal destructs an active counter', () => {
  const f = fixture(); f.run(); f.events.allow();
  const pending = f.calls[0]; f.events.preferences(); f.events.deny(); pending.onload();
  assert.equal(f.win.ym.a.some(args => args[1] === 'init'), false);
  const active = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_800_000_000_000 } });
  active.run(); active.calls[0].onload(); active.events.preferences(); active.events.deny();
  assert.equal(active.win.ym.a.some(args => args[1] === 'destruct'), true);
});

test('stored acceptance is probed without extending its age; failed refusal cannot revive it on reload', () => {
  const f = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_799_999_000_000 } });
  const controller = f.run();
  assert.equal(f.calls.length, 1);
  assert.equal(JSON.parse(f.values.get(KEY)).savedAt, 1_799_999_000_000);
  f.calls[0].onload();
  f.blockWrites();
  f.events.preferences();
  f.events.deny();
  assert.equal(f.win.ym.a.some(args => args[1] === 'destruct'), true);
  assert.match(f.panel.querySelector('[data-analytics-status]').textContent, /не смог сохранить отказ/);
  assert.equal(f.panel.hidden, false);

  const reload = fixture({ stored: f.values.get(KEY) });
  reload.blockWrites();
  reload.run();
  assert.equal(reload.calls.length, 0);
  assert.equal(reload.panel.hidden, false);

  const api = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_799_999_000_000 } });
  const apiController = api.run();
  api.blockWrites();
  assert.equal(apiController.revoke(), false);
  assert.equal(api.calls.length, 1);
  const apiReload = fixture({ stored: api.values.get(KEY) });
  apiReload.blockWrites();
  apiReload.run();
  assert.equal(apiReload.calls.length, 0);
});

test('a saved acceptance is not honored when the same-value storage probe fails', () => {
  const f = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_799_999_000_000 } });
  f.blockWrites(); f.run();
  assert.equal(f.calls.length, 0);
  assert.equal(f.panel.hidden, false);
  assert.match(f.panel.querySelector('[data-analytics-status]').textContent, /останется выключенной/);
});

test('a stale script load cannot initialize after refusal and a later new consent', () => {
  const f = fixture(); f.run(); f.events.allow();
  const stale = f.calls[0];
  f.events.preferences(); f.events.deny();
  f.events.preferences(); f.events.allow();
  const current = f.calls[1];
  stale.onload();
  assert.equal(f.win.ym.a.some(args => args[1] === 'init'), false);
  current.onload();
  assert.equal(f.win.ym.a.filter(args => args[1] === 'init').length, 1);
});

test('a refusal in another tab destructs an initialized counter without rewriting consent', () => {
  const first = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_800_000_000_000 } });
  first.run(); first.calls[0].onload();
  const sharedValues = first.values;
  let writes = 0;
  const second = fixture({ sharedValues });
  const originalSet = second.storage.setItem;
  second.storage.setItem = (...args) => { writes++; originalSet(...args); };
  second.run(); writes = 0; second.events.deny();
  const rejected = second.values.get(KEY);
  first.win.dispatch('storage', { key: KEY, newValue: rejected });
  assert.equal(first.win.ym.a.some(args => args[1] === 'destruct'), true);
  assert.equal(first.calls[0].parentNode, null);
  assert.equal(first.values.get(KEY), rejected);
  assert.equal(writes, 1);
});

test('storage clearing and expired consent stop analytics on storage, focus, and visibility return', () => {
  const cleared = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_800_000_000_000 } });
  cleared.run(); cleared.calls[0].onload(); cleared.values.delete(KEY);
  cleared.win.dispatch('storage', { key: KEY, newValue: null });
  assert.equal(cleared.win.ym.a.some(args => args[1] === 'destruct'), true);

  const expired = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_800_000_000_000 } });
  expired.run(); expired.calls[0].onload(); expired.setNow(1_800_000_000_000 + 90 * 24 * 60 * 60 * 1000);
  expired.win.dispatch('focus', {});
  assert.equal(expired.win.ym.a.some(args => args[1] === 'destruct'), true);
  assert.equal(expired.panel.hidden, false);

  const hidden = fixture({ stored: { version: 1, decision: 'accepted', savedAt: 1_800_000_000_000 } });
  hidden.run(); hidden.calls[0].onload(); hidden.setNow(1_800_000_000_000 + 90 * 24 * 60 * 60 * 1000);
  hidden.doc.hidden = false; hidden.events.visibilitychange?.();
  assert.equal(hidden.win.ym.a.some(args => args[1] === 'destruct'), true);
});

test('the module is limited to production and the source masks forms and search inputs', async () => {
  const demo = fixture({ hostname: 'demo.example' }); demo.run();
  assert.equal(demo.calls.length, 0); assert.equal(demo.panel.hidden, true);
  const build = await readFile(new URL('../build.py', import.meta.url), 'utf8');
  assert.match(build, /analytics_enabled=indexable and origin=='https:\/\/engine\.cmteh\.ru'/);
  assert.match(build, /order-form ym-hide-content/); assert.match(build, /class="ym-disable-keys" name="name"/);
  assert.match(build, /class="ym-disable-keys" name="contact"/); assert.match(build, /class="ym-disable-keys" name="comment"/);
  assert.match(build, /class="ym-disable-keys" id="catalog-search"/); assert.match(build, /class="ym-disable-keys" id="hero-query"/);
});
