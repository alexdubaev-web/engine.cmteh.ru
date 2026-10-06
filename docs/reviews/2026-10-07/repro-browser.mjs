import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const analyticsSource = (await readFile(`${root}/public/assets/analytics.js`, 'utf8'))
  .replace('export function createAnalyticsConsent', 'function createAnalyticsConsent')
  .replace(/\ntry \{ createAnalyticsConsent\([\s\S]*$/, '\nglobalThis.createAnalyticsConsent = createAnalyticsConsent;');
const appSource = await readFile(`${root}/public/assets/app.js`, 'utf8');
const consentKey = 'cmteh.analytics-consent.v1';
const cartKey = 'cm-techno-cart';
const now = 1_800_000_000_000;

// Real analytics.js module, two VM windows/documents, shared localStorage.
const sharedValues = new Map();
function analyticsTab() {
  const events = {};
  const calls = [];
  const status = { textContent: '' };
  const allow = { focus() {}, addEventListener: (_type, fn) => events.allow = fn };
  const deny = { addEventListener: (_type, fn) => events.deny = fn };
  const panel = { hidden: true, querySelector: selector => selector.includes('allow') ? allow : selector.includes('deny') ? deny : status };
  const head = { appendChild(node) { node.parentNode = head; calls.push(node); }, removeChild(node) { node.parentNode = null; } };
  const doc = { referrer: '', head, querySelector: () => panel, querySelectorAll: () => [{ addEventListener: (_type, fn) => events.preferences = fn }], createElement: () => ({}) };
  const win = { location: { hostname: 'engine.cmteh.ru', origin: 'https://engine.cmteh.ru', pathname: '/' }, addEventListener: (_type, fn) => events.keydown = fn };
  const storage = { getItem: k => sharedValues.get(k) ?? null, setItem: (k, v) => sharedValues.set(k, v), removeItem: k => sharedValues.delete(k) };
  const context = vm.createContext({ URL, Date, JSON, Number });
  vm.runInContext(analyticsSource, context);
  return { events, calls, panel, win, controller: context.createAnalyticsConsent({ window: win, document: doc, storage, now: () => now }) };
}
const tabA = analyticsTab();
tabA.events.allow(); tabA.calls[0].onload();
assert.equal(tabA.win.ym.a.some(args => args[1] === 'init'), true);
const tabB = analyticsTab();
tabB.events.preferences(); tabB.events.deny();
assert.equal(JSON.parse(sharedValues.get(consentKey)).decision, 'rejected');
assert.equal(tabA.win.ym.a.some(args => args[1] === 'destruct'), false);
assert.equal(analyticsSource.includes("addEventListener('storage'"), false);
console.log('PASS analytics: real analytics.js VM repro — tab B refusal persists, initialized tab A tracker receives no destruct');

// Minimal browser storage-event queue using app.js's private-cart replacement and saveCart writeback behavior.
assert.match(appSource, /const stored=JSON\.parse\(localStorage\.getItem\('cm-techno-cart'\)\|\|'\[\]'\)/);
assert.match(appSource, /function saveCart\(\)\{try\{localStorage\.setItem\('cm-techno-cart',JSON\.stringify\(cart\)\)/);
assert.match(appSource, /window\.addEventListener\('storage',e=>\{if\(e\.key==='cm-techno-cart'/);
const values = new Map([[cartKey, '[]']]);
const tabs = new Map();
const queue = [];
let eventCount = 0;
function write(key, value, source) {
  const oldValue = values.get(key) ?? null;
  if (oldValue === value) return; // Web Storage does not notify for same-value writes.
  values.set(key, value);
  for (const [name, tab] of tabs) if (name !== source) queue.push({ name, key, oldValue, newValue: value });
}
function makeCartTab(name) {
  const tab = { cart: JSON.parse(values.get(cartKey) || '[]') };
  tabs.set(name, tab);
  tab.add = id => { const item = tab.cart.find(x => x.id === id); if (item) item.quantity = Math.min(999, item.quantity + 1); else tab.cart.push({ id, quantity: 1 }); tab.save(); };
  tab.save = () => write(cartKey, JSON.stringify(tab.cart), name);
  tab.onStorage = event => {
    if (event.key !== cartKey) return;
    try {
      const v = JSON.parse(event.newValue || '[]');
      if (Array.isArray(v)) { tab.cart = v.filter(x => x && typeof x.id === 'string' && Number.isInteger(x.quantity) && x.quantity > 0 && x.quantity <= 999); tab.save(); }
    } catch {}
  };
  return tab;
}
const cartA = makeCartTab('A');
const cartB = makeCartTab('B');
cartA.add('product-a');
cartB.add('product-b');
let iterations = 0;
while (queue.length && iterations < 100) {
  const event = queue.shift(); eventCount++; iterations++;
  tabs.get(event.name).onStorage(event);
}
assert.ok(eventCount >= 100, `expected repeating event feedback, got ${eventCount}`);
assert.ok(queue.length > 0, 'feedback queue should remain nonempty');
assert.equal(JSON.parse(values.get(cartKey)).length, 1);
assert.ok(cartA.cart.length === 1 && cartB.cart.length === 1);
console.log(`PASS cart multi-tab repro: two adds from [] lose an item; storage handler saveCart writeback generated ${eventCount} events with ${queue.length} still queued`);

// Model the production submit-time snapshot and success clear around deferred fetch.
assert.match(appSource, /data\.items=selectedItems\(form\)/);
assert.match(appSource, /if\(form\.dataset\.kind==='cart'\)\{cart=\[\];saveCart\(\)\}/);
let liveCart = [{ id: 'product-a', quantity: 1 }];
const submittedItems = liveCart.map(x => ({ ...x }));
liveCart.push({ id: 'product-b', quantity: 1 }); // cart controls remain enabled while fetch is pending
liveCart = []; // production success path clears the entire live cart
assert.deepEqual(submittedItems.map(x => x.id), ['product-a']);
assert.deepEqual(liveCart, []);
assert.equal(submittedItems.some(x => x.id === 'product-b'), false);
console.log('PASS submit race model: item added while request is pending is omitted from snapshot then erased by success clear');
