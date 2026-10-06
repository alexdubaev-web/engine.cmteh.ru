import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { JSDOM, VirtualConsole } from 'jsdom';
import { IDBFactory } from 'fake-indexeddb';
import { webcrypto } from 'node:crypto';

const source = await readFile(process.env.APP_SOURCE || new URL('../public/assets/app.js', import.meta.url), 'utf8');
const products = [
  { id: 'product-a', sku: 'A', brand: 'Brand', name: 'Part A', price: 10 },
  { id: 'product-b', sku: 'B', brand: 'Brand', name: 'Part B', price: 20 }
];
function makeBroadcastChannel(bus) {
  return class TestBroadcastChannel {
    constructor(name) { this.name = name; this.listeners = new Set(); const peers = bus.get(name) || new Set(); peers.add(this); bus.set(name, peers); }
    addEventListener(type, listener) { if (type === 'message') this.listeners.add(listener); }
    postMessage(data) { for (const peer of bus.get(this.name) || []) if (peer !== this) for (const listener of peer.listeners) listener({ data }); }
    close() { bus.get(this.name)?.delete(this); }
  };
}

function makeTab({ indexedDB, fetchImpl, seed = '[]', channelBus = new Map() }) {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  const html = `<!doctype html><body>
    <script id="catalog-data" type="application/json">${JSON.stringify(products)}</script>
    <dialog id="cart-dialog"><button data-cart-close></button><div id="cart-items"></div><div id="cart-totals"></div></dialog>
    <span data-cart-count></span><button data-cart-open></button>
    <form class="order-form" data-kind="cart">
      <input name="name" value="Initial"><input name="contact" value="user@example.com">
      <input name="comment" value=""><input type="checkbox" name="consent" checked>
      <input type="hidden" name="consentVersion" value="1">
      <button type="submit">Send</button><p class="form-status"></p>
      <button type="button" data-export hidden></button><label class="consent"></label>
    </form>
    <button class="menu-toggle" aria-expanded="false"></button><nav id="navigation" class="nav"></nav>
    <div class="toast"></div><header class="header"></header>
    <button data-add="product-a">Add A</button><button data-add="product-b">Add B</button>
  </body>`;
  const dom = new JSDOM(html, { url: 'https://engine.cmteh.ru/', runScripts: 'outside-only', virtualConsole });
  const { window } = dom;
  Object.defineProperty(window, 'indexedDB', { value: indexedDB });
  Object.defineProperty(window, 'crypto', { value: webcrypto });
  Object.defineProperty(window, 'BroadcastChannel', { value: makeBroadcastChannel(channelBus) });
  window.matchMedia = () => ({ matches: true, addEventListener() {} });
  window.fetch = fetchImpl;
  window.AbortSignal.timeout = () => new AbortController().signal;
  window.localStorage.setItem('cm-techno-cart', seed);
  window.eval(source);
  return { dom, window, document: window.document, errors };
}

const tick = () => new Promise(resolve => setTimeout(resolve, 250));
async function waitFor(predicate) { for (let i = 0; i < 100; i++) { if (predicate()) return true; await new Promise(resolve => setTimeout(resolve, 20)); } return false; }
function readCartRecord(factory) { return new Promise((resolve, reject) => { const open = factory.open('cm-techno-cart-v1'); open.onerror = () => reject(open.error); open.onsuccess = () => { const db = open.result, tx = db.transaction('state', 'readonly'), request = tx.objectStore('state').get('cart'); request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error); tx.oncomplete = () => db.close(); }; }); }
const configResponse = () => Promise.resolve({ ok: true, json: async () => ({ submissionEnabled: true, consentVersion: '1', csrfToken: 'test' }) });
function failOneCartTransaction(factory) {
  let failNext = false;
  const wrapped = { failNext() { failNext = true; }, open(...args) {
    const request = factory.open(...args);
    return new Proxy(request, { get(target, property) {
      if (property === 'result') return new Proxy(target.result, { get(db, key) {
        if (key === 'transaction') return (...transactionArgs) => {
          if (failNext) { failNext = false; throw new Error('Injected IndexedDB failure'); }
          return db.transaction(...transactionArgs);
        };
        const value = Reflect.get(db, key, db);
        return typeof value === 'function' ? value.bind(db) : value;
      } });
      const value = Reflect.get(target, property, target);
      return typeof value === 'function' ? value.bind(target) : value;
    } });
  } };
  return wrapped;
}
function delayOpenSuccess(factory, delayMs) {
  return { open(...args) {
    const request = factory.open(...args);
    return new Proxy(request, { set(target, property, value) {
      if (property === 'onsuccess') return Reflect.set(target, property, function (event) { setTimeout(() => value.call(target, event), delayMs); });
      return Reflect.set(target, property, value);
    }, get(target, property) {
      const value = Reflect.get(target, property, target);
      return typeof value === 'function' ? value.bind(target) : value;
    } });
  } };
}
function abortOneCartWrite(factory) {
  let abortNext = false, aborted = 0;
  const wrapped = { get abortCount() { return aborted; }, abortNextWrite() { abortNext = true; }, open(...args) {
    const request = factory.open(...args);
    return new Proxy(request, { get(target, property) {
      if (property === 'result') return new Proxy(target.result, { get(db, key) {
        if (key === 'transaction') return (...transactionArgs) => {
          const tx = db.transaction(...transactionArgs);
          return new Proxy(tx, { get(transaction, txKey) {
            if (txKey === 'objectStore') return name => {
              const store = transaction.objectStore(name);
              return new Proxy(store, { get(objectStore, storeKey) {
                if (storeKey === 'put') return (...putArgs) => {
                  const result = objectStore.put(...putArgs);
                  if (abortNext) { abortNext = false; aborted++; transaction.abort(); }
                  return result;
                };
                const value = Reflect.get(objectStore, storeKey, objectStore);
                return typeof value === 'function' ? value.bind(objectStore) : value;
              } });
            };
            const value = Reflect.get(transaction, txKey, transaction);
            return typeof value === 'function' ? value.bind(transaction) : value;
          } });
        };
        const value = Reflect.get(db, key, db);
        return typeof value === 'function' ? value.bind(db) : value;
      } });
      const value = Reflect.get(target, property, target);
      return typeof value === 'function' ? value.bind(target) : value;
    } });
  } };
  return wrapped;
}

test('concurrent cart additions in separate tabs are serialized and reload-only notifications converge', async () => {
  const indexedDB = new IDBFactory();
  const channelBus = new Map();
  const fetchImpl = () => configResponse();
  const first = makeTab({ indexedDB, fetchImpl, channelBus });
  const second = makeTab({ indexedDB, fetchImpl, channelBus });
  await tick();
  first.document.querySelector('[data-add="product-a"]').click();
  second.document.querySelector('[data-add="product-b"]').click();
  await new Promise(resolve => setTimeout(resolve, 250)); await tick();
  const reload = makeTab({ indexedDB, fetchImpl, seed: '[]', channelBus });
  await waitFor(() => reload.document.querySelector('[data-cart-count]').textContent === '2');
  await waitFor(() => first.document.querySelector('[data-cart-count]').textContent === '2' && second.document.querySelector('[data-cart-count]').textContent === '2');
  const cartText = reload.document.querySelector('#cart-items').textContent;
  assert.deepEqual(reload.errors, []);
  assert.match(cartText, /Part A/);
  assert.match(cartText, /Part B/);
  assert.equal(reload.document.querySelector('[data-cart-count]').textContent, '2');
  first.dom.window.close(); second.dom.window.close(); reload.dom.window.close();
});

test('a delayed second initialization cannot replace current data with its stale legacy cart', async () => {
  const indexedDB = new IDBFactory(), channelBus = new Map();
  const fetchImpl = () => configResponse();
  const first = makeTab({ indexedDB, fetchImpl, channelBus, seed: '[]' });
  assert.ok(await waitFor(() => first.document.querySelector('[data-cart-count]').textContent === '0'));
  first.document.querySelector('[data-add="product-a"]').click();
  assert.ok(await waitFor(() => first.document.querySelector('[data-cart-count]').textContent === '1'));
  const delayedSecond = makeTab({ indexedDB: delayOpenSuccess(indexedDB, 80), fetchImpl, channelBus, seed: JSON.stringify([{ id: 'product-b', quantity: 1 }]) });
  assert.ok(await waitFor(() => /Part A/.test(delayedSecond.document.querySelector('#cart-items').textContent)));
  assert.doesNotMatch(delayedSecond.document.querySelector('#cart-items').textContent, /Part B/);
  first.dom.window.close(); delayedSecond.dom.window.close();
});

test('add followed immediately by submit includes the pending cart mutation', async () => {
  const indexedDB = new IDBFactory();
  let resolveOrder, payload;
  const fetchImpl = (url, options) => url === '/api/orders.php'
    ? (payload = JSON.parse(options.body), new Promise(resolve => { resolveOrder = resolve; }))
    : configResponse();
  const tab = makeTab({ indexedDB, fetchImpl });
  tab.document.querySelector('[data-add="product-a"]').click();
  const form = tab.document.querySelector('.order-form');
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  const reachedOrder = await waitFor(() => typeof resolveOrder === 'function');
  assert.ok(reachedOrder, `status=${form.querySelector('.form-status').textContent}`);
  assert.deepEqual(payload.items, [{ id: 'product-a', quantity: 1 }]);
  resolveOrder({ ok: true, json: async () => ({ ok: true, message: 'Accepted', requestId: 'request-123' }) });
  await waitFor(() => form.querySelector('.form-status').textContent.includes('request-1'));
  await tick();
  tab.dom.window.close();
});

test('successful submit preserves cart and form edits made while the request is pending', async () => {
  const indexedDB = new IDBFactory();
  let resolveOrder;
  const fetchImpl = url => url === '/api/orders.php'
    ? new Promise(resolve => { resolveOrder = resolve; })
    : configResponse();
  const tab = makeTab({ indexedDB, fetchImpl, seed: JSON.stringify([{ id: 'product-a', quantity: 1 }]) });
  await waitFor(() => /Part A/.test(tab.document.querySelector('#cart-items').textContent));
  const { document } = tab;
  const form = document.querySelector('.order-form');
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  const reachedOrder = await waitFor(() => typeof resolveOrder === 'function');
  assert.ok(reachedOrder, `status=${form.querySelector('.form-status').textContent}; errors=${JSON.stringify(tab.errors)}`);
  document.querySelector('[data-add="product-b"]').click();
  form.elements.name.value = 'Edited while sending';
  form.elements.name.dispatchEvent(new tab.window.Event('input', { bubbles: true }));
  resolveOrder({ ok: true, json: async () => ({ ok: true, message: 'Accepted', requestId: 'request-123' }) });
  await waitFor(() => tab.document.querySelector('.form-status').textContent.includes('request-1'));
  assert.match(document.querySelector('#cart-items').textContent, /Part A/);
  assert.match(document.querySelector('#cart-items').textContent, /Part B/);
  assert.equal(form.elements.name.value, 'Edited while sending');
  await tick();
  tab.dom.window.close();
});

test('clear uses the submitted revision and does not erase an ABA remove-and-readd', async () => {
  const indexedDB = new IDBFactory();
  let resolveOrder;
  const fetchImpl = url => url === '/api/orders.php'
    ? new Promise(resolve => { resolveOrder = resolve; })
    : configResponse();
  const tab = makeTab({ indexedDB, fetchImpl, seed: JSON.stringify([{ id: 'product-a', quantity: 1 }]) });
  await waitFor(() => /Part A/.test(tab.document.querySelector('#cart-items').textContent));
  const form = tab.document.querySelector('.order-form');
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.ok(await waitFor(() => typeof resolveOrder === 'function'));
  tab.document.querySelector('[data-remove="product-a"]').click();
  await waitFor(() => tab.document.querySelector('[data-cart-count]').textContent === '0');
  tab.document.querySelector('[data-add="product-a"]').click();
  await waitFor(() => /Part A/.test(tab.document.querySelector('#cart-items').textContent));
  resolveOrder({ ok: true, json: async () => ({ ok: true, message: 'Accepted', requestId: 'request-123' }) });
  await waitFor(() => form.querySelector('.form-status').textContent.includes('request-1'));
  assert.match(tab.document.querySelector('#cart-items').textContent, /Part A/);
  await tick();
  tab.dom.window.close();
});

test('an empty committed cart does not resurrect legacy items and remains usable without IndexedDB', async () => {
  const indexedDB = new IDBFactory();
  const fetchImpl = url => url === '/api/orders.php'
    ? Promise.resolve({ ok: true, json: async () => ({ ok: true, message: 'Accepted', requestId: 'request-123' }) })
    : configResponse();
  const first = makeTab({ indexedDB, fetchImpl, seed: JSON.stringify([{ id: 'product-a', quantity: 1 }]) });
  await waitFor(() => /Part A/.test(first.document.querySelector('#cart-items').textContent));
  const form = first.document.querySelector('.order-form');
  form.dispatchEvent(new first.window.Event('submit', { bubbles: true, cancelable: true }));
  await waitFor(() => first.document.querySelector('[data-cart-count]').textContent === '0');
  const reload = makeTab({ indexedDB, fetchImpl, seed: JSON.stringify([{ id: 'product-a', quantity: 1 }]) });
  await waitFor(() => reload.document.querySelector('[data-cart-count]').textContent === '0');
  assert.doesNotMatch(reload.document.querySelector('#cart-items').textContent, /Part A/);
  const fallback = makeTab({ indexedDB: null, fetchImpl });
  fallback.document.querySelector('[data-add="product-b"]').click();
  assert.ok(await waitFor(() => /Part B/.test(fallback.document.querySelector('#cart-items').textContent)));
  assert.equal(fallback.document.querySelector('[data-cart-count]').textContent, '1');
  first.dom.window.close(); reload.dom.window.close(); fallback.dom.window.close();
});

test('cart switches to in-memory operation when an established IndexedDB connection fails', async () => {
  const indexedDB = failOneCartTransaction(new IDBFactory());
  const tab = makeTab({ indexedDB, fetchImpl: () => configResponse() });
  assert.ok(await waitFor(() => tab.document.querySelector('[data-cart-count]').textContent === '0'));
  indexedDB.failNext();
  tab.document.querySelector('[data-add="product-b"]').click();
  assert.ok(await waitFor(() => /Part B/.test(tab.document.querySelector('#cart-items').textContent)));
  assert.equal(tab.document.querySelector('[data-cart-count]').textContent, '1');
  tab.document.querySelector('[data-add="product-a"]').click();
  assert.ok(await waitFor(() => /Part A/.test(tab.document.querySelector('#cart-items').textContent)));
  assert.equal(tab.document.querySelector('[data-cart-count]').textContent, '2');
  tab.dom.window.close();
});

test('an asynchronous IndexedDB abort applies an add only once before memory fallback', async () => {
  const indexedDB = abortOneCartWrite(new IDBFactory());
  const tab = makeTab({ indexedDB, fetchImpl: () => configResponse() });
  assert.ok(await waitFor(() => tab.document.querySelector('[data-cart-count]').textContent === '0'));
  assert.deepEqual((await readCartRecord(indexedDB)).items, []);
  indexedDB.abortNextWrite();
  tab.document.querySelector('[data-add="product-a"]').click();
  assert.ok(await waitFor(() => tab.document.querySelector('[data-cart-count]').textContent !== '0'));
  await tick();
  assert.equal(indexedDB.abortCount, 1);
  assert.equal(tab.document.querySelector('[data-cart-count]').textContent, '1');
  tab.document.querySelector('[data-add="product-b"]').click();
  assert.ok(await waitFor(() => tab.document.querySelector('[data-cart-count]').textContent === '2'));
  tab.dom.window.close();
});
