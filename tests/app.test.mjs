import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { JSDOM, VirtualConsole } from 'jsdom';
import { IDBFactory } from 'fake-indexeddb';
import { webcrypto } from 'node:crypto';

const source = await readFile(process.env.APP_SOURCE || new URL('../public/assets/app.js', import.meta.url), 'utf8');
const products = [
  { id: 'product-a', sku: '0445020110', codes: ['0445020110'], brand: 'Bosch', name: 'Part A', category: 'pumps', price: 10 },
  { id: 'product-b', sku: '0445120075', codes: ['0445120075'], brand: 'Delphi', name: 'Part B', category: 'injectors', price: 20 },
  { id: 'product-c', sku: '121000-1234', codes: ['121000-1234'], brand: 'Denso', name: 'Part C', category: 'pumps', price: 30 }
];
function makeBroadcastChannel(bus) {
  return class TestBroadcastChannel {
    constructor(name) { this.name = name; this.listeners = new Set(); const peers = bus.get(name) || new Set(); peers.add(this); bus.set(name, peers); }
    addEventListener(type, listener) { if (type === 'message') this.listeners.add(listener); }
    postMessage(data) { for (const peer of bus.get(this.name) || []) if (peer !== this) for (const listener of peer.listeners) listener({ data }); }
    close() { bus.get(this.name)?.delete(this); }
  };
}

function makeTab({ indexedDB, fetchImpl, seed = '[]', sessionSeed = null, channelBus = new Map(), catalog = false, kind = 'cart', productId = '' }) {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  const catalogHtml = catalog ? `<section class="catalog" data-limit="20" data-default-category="">
    <input id="catalog-search"><select id="brand-filter"><option value="">All brands</option><option>Bosch</option><option>Delphi</option><option>Denso</option></select>
    <select id="sort-filter"><option value="default">Default</option></select>
    <div class="tabs"><a data-filter="" href="#">All</a><a data-filter="pumps" href="#">Pumps</a><a data-filter="injectors" href="#">Injectors</a></div>
    <div id="product-grid">${products.map(p => `<article class="product-card" data-id="${p.id}" data-category="${p.category}" data-brand="${p.brand}" data-price="${p.price}" data-search="${[...p.codes, p.name, p.brand].join(' ')}"></article>`).join('')}</div>
    <span id="result-count"></span><button id="show-more" hidden></button>
    <div class="empty-state" hidden><span>No results</span><a href="#selection" data-inquiry-search>Ask about this part</a><button data-reset>Reset</button></div>
  </section>` : '';
  const html = `<!doctype html><body>
    <script id="catalog-data" type="application/json">${JSON.stringify(products)}</script>
    ${catalogHtml}
    <dialog id="cart-dialog"><button data-cart-close></button><div id="cart-items"></div><div id="cart-totals"></div></dialog>
    <span data-cart-count></span><button data-cart-open></button>
    <form id="selection" class="order-form" data-kind="${kind}" ${productId ? `data-product-id="${productId}"` : ''}>
      <input name="name" value="Initial" required><input name="contact" value="user@example.com" required>
      <input name="comment" value=""><input type="checkbox" name="consent" checked required>
      <input type="hidden" name="consentVersion" value="1">
      <button type="submit">Send</button><p class="form-status"></p>
      <button type="button" data-export hidden></button><label class="consent"></label>
    </form>
    <button class="menu-toggle" aria-expanded="false"></button><nav id="navigation" class="nav"></nav>
    <div class="toast"></div><header class="header"></header>
    <button data-add="product-a">Add A</button><button data-add="product-b">Add B</button><button data-add="product-c">Add C</button>
  </body>`;
  const dom = new JSDOM(html, { url: catalog ? 'https://engine.cmteh.ru/catalog/' : 'https://engine.cmteh.ru/', runScripts: 'outside-only', virtualConsole });
  const { window } = dom;
  Object.defineProperty(window, 'indexedDB', { value: indexedDB });
  Object.defineProperty(window, 'crypto', { value: webcrypto });
  Object.defineProperty(window, 'BroadcastChannel', { value: makeBroadcastChannel(channelBus) });
  window.matchMedia = () => ({ matches: true, addEventListener() {} });
  window.fetch = fetchImpl;
  window.AbortSignal.timeout = () => new AbortController().signal;
  window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  window.URL.createObjectURL = () => 'blob:test'; window.URL.revokeObjectURL = () => {};
  const anchorClick = window.HTMLAnchorElement.prototype.click;
  window.HTMLAnchorElement.prototype.click = function () { if (this.hasAttribute('download')) { this.dataset.clicked = 'true'; return; } return anchorClick.call(this); };
  window.localStorage.setItem('cm-techno-cart', seed);
  if (sessionSeed !== null) window.sessionStorage.setItem('cm-techno-cart-quantity-checkpoint', sessionSeed);
  window.eval(source);
  return { dom, window, document: window.document, errors };
}

const tick = () => new Promise(resolve => setTimeout(resolve, 250));
async function waitFor(predicate) { for (let i = 0; i < 100; i++) { if (predicate()) return true; await new Promise(resolve => setTimeout(resolve, 20)); } return false; }
function readCartRecord(factory) { return new Promise((resolve, reject) => { const open = factory.open('cm-techno-cart-v1'); open.onerror = () => reject(open.error); open.onsuccess = () => { const db = open.result, tx = db.transaction('state', 'readonly'), request = tx.objectStore('state').get('cart'); request.onsuccess = () => resolve(request.result); request.onerror = () => reject(request.error); tx.oncomplete = () => db.close(); }; }); }
function writeCartRecord(factory, record) { return new Promise((resolve, reject) => { const open = factory.open('cm-techno-cart-v1'); open.onupgradeneeded = () => open.result.createObjectStore('state'); open.onerror = () => reject(open.error); open.onsuccess = () => { const db = open.result, tx = db.transaction('state', 'readwrite'); tx.objectStore('state').put(record, 'cart'); tx.oncomplete = () => { db.close(); resolve(); }; tx.onerror = tx.onabort = () => { db.close(); reject(tx.error); }; }; }); }
async function waitForCartRecord(factory, predicate) { for (let i = 0; i < 100; i++) { const record = await readCartRecord(factory); if (predicate(record)) return record; await new Promise(resolve => setTimeout(resolve, 20)); } return null; }
const configResponse = () => Promise.resolve({ ok: true, json: async () => ({ submissionEnabled: true, consentVersion: '1', csrfToken: 'test' }) });
const acceptedOrderResponse = (requestId, fields = {}) => Promise.resolve({ ok: true, json: async () => ({ ok: true, message: 'Accepted', requestId, orderNumber: 42, createdAt: Date.parse('2026-10-06T21:30:00Z') / 1000, ...fields }) });

test('catalog search matches aliases, unordered tokens, punctuated article codes, and current category', async () => {
  const fetchCalls = [], tab = makeTab({ indexedDB: new IDBFactory(), catalog: true, fetchImpl: (...args) => { fetchCalls.push(args); return configResponse(); } });
  const { document, window } = tab, input = document.querySelector('#catalog-search');
  await tick();
  assert.deepEqual(fetchCalls, [], 'opening a catalog page does not request submission config');
  const search = value => { input.value = value; input.dispatchEvent(new window.Event('input', { bubbles: true })); return [...document.querySelectorAll('.product-card:not([hidden])')].map(card => card.dataset.id); };
  assert.deepEqual(search('Bosch 0445-020-110'), ['product-a']);
  assert.deepEqual(search('0445 020110'), ['product-a']);
  assert.deepEqual(search('Бош'), ['product-a']);
  assert.deepEqual(search('Делфи'), ['product-b']);
  assert.deepEqual(search('Денсо'), ['product-c']);
  document.querySelector('[data-filter="injectors"]').click();
  assert.deepEqual([...document.querySelectorAll('.product-card:not([hidden])')].map(card => card.dataset.id), []);
  assert.equal(document.querySelector('.empty-state').hidden, false);
  const resetEvent = new window.Event('click', { bubbles: true, cancelable: true });
  document.querySelector('[data-reset]').dispatchEvent(resetEvent);
  assert.equal(input.value, '');
  assert.equal(document.querySelector('.empty-state').hidden, true);
  await tick(); tab.dom.window.close();
});

test('no-results inquiry link pre-fills the description with the current search', async () => {
  const tab = makeTab({ indexedDB: new IDBFactory(), catalog: true, kind: 'inquiry', fetchImpl: () => configResponse() });
  const { document, window } = tab, input = document.querySelector('#catalog-search');
  input.value = 'XY-999 injector'; input.dispatchEvent(new window.Event('input', { bubbles: true }));
  document.querySelector('[data-inquiry-search]').click();
  assert.equal(document.querySelector('[name="comment"]').value, 'XY-999 injector');
  assert.equal(document.querySelector('[data-inquiry-search]').hash, '#selection');
  await tick(); tab.dom.window.close();
});

test('inquiry from a product card includes that product in the submitted items', async () => {
  let submitted;
  const events = [], tab = makeTab({ indexedDB: new IDBFactory(), kind: 'inquiry', productId: 'product-a', fetchImpl: (url, options) => {
    if (url === '/api/orders.php') { submitted = JSON.parse(options.body); return acceptedOrderResponse(submitted.requestId); }
    return configResponse();
  } });
  tab.document.addEventListener('cm:analytics', event => events.push(event.detail));
  const form = tab.document.querySelector('.order-form');
  form.dispatchEvent(new tab.window.Event('input', { bubbles: true }));
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.ok(await waitFor(() => submitted));
  assert.deepEqual(submitted.items, [{ id: 'product-a', quantity: 1 }]);
  assert.ok(await waitFor(() => events.some(event => event.name === 'form_success' && event.params.kind === 'inquiry')));
  await tick(); tab.dom.window.close();
});

test('search and cart analytics events contain only approved non-personal parameters', async () => {
  const events = [], tab = makeTab({ indexedDB: new IDBFactory(), catalog: true, fetchImpl: () => configResponse() });
  tab.document.addEventListener('cm:analytics', event => events.push(event.detail));
  const input = tab.document.querySelector('#catalog-search');
  input.value = 'no-such'; input.dispatchEvent(new tab.window.Event('input', { bubbles: true }));
  input.value = 'no-such-part'; input.dispatchEvent(new tab.window.Event('input', { bubbles: true }));
  assert.equal(events.length, 0, 'search events wait until typing pauses');
  assert.ok(await waitFor(() => events.some(event => event.name === 'search_empty')));
  assert.equal(events.filter(event => event.name === 'search').length, 1);
  assert.ok(events.some(event => event.name === 'search' && event.params.result_count === 0 && !('query' in event.params)));
  assert.ok(events.some(event => event.name === 'search_empty' && event.params.result_count === 0 && !('query' in event.params)));
  const searchEventCount = events.length;
  tab.document.querySelector('[data-reset]').click();
  const sort = tab.document.querySelector('#sort-filter'); sort.dispatchEvent(new tab.window.Event('change', { bubbles: true }));
  tab.document.querySelector('#show-more').click();
  assert.equal(events.length, searchEventCount, 'reset, sorting, and pagination do not create search events');
  tab.document.querySelector('[data-add="product-a"]').click();
  tab.document.querySelector('[data-cart-open]').click();
  await waitFor(() => events.some(event => event.name === 'add_to_cart'));
  assert.ok(events.some(event => event.name === 'add_to_cart' && event.params.sku === '0445020110' && event.params.quantity === 1));
  assert.ok(events.some(event => event.name === 'cart_open'));
  assert.ok(events.every(event => !JSON.stringify(event).includes('no-such-part')));
  await tick(); tab.dom.window.close();
});

test('invalid inquiry reports a non-personal form error and does not submit', async () => {
  let orderRequests = 0; const events = [];
  const tab = makeTab({ indexedDB: new IDBFactory(), kind: 'inquiry', fetchImpl: url => { if (url === '/api/orders.php') orderRequests++; return configResponse(); } });
  tab.document.addEventListener('cm:analytics', event => events.push(event.detail));
  const form = tab.document.querySelector('.order-form');
  form.elements.contact.value = 'not-an-email'; form.elements.comment.value = 'Need help';
  form.dispatchEvent(new tab.window.Event('input', { bubbles: true }));
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.equal(orderRequests, 0);
  assert.ok(events.some(event => event.name === 'form_start' && event.params.kind === 'inquiry'));
  assert.ok(events.some(event => event.name === 'form_error' && event.params.kind === 'inquiry' && event.params.reason === 'contact_format'));
  assert.ok(events.every(event => !JSON.stringify(event).includes('not-an-email')));
  await tick(); tab.dom.window.close();
});

test('malformed or mismatched success responses are not accepted or tracked', async t => {
  const cases = [
    ['truthy non-boolean ok', requestId => ({ ok: 'true', requestId, createdAt: 1791322200, orderNumber: 42 })],
    ['foreign request id', requestId => ({ ok: true, requestId: '00000000-0000-4000-8000-000000000000', createdAt: 1791322200, orderNumber: 42 })],
    ['missing timestamp', requestId => ({ ok: true, requestId, orderNumber: 42 })],
    ['unrepresentable timestamp', requestId => ({ ok: true, requestId, createdAt: Number.MAX_SAFE_INTEGER, orderNumber: 42 })],
    ['invalid order number', requestId => ({ ok: true, requestId, createdAt: 1791322200, orderNumber: 0 })],
    ['array response', () => []]
  ];
  for (const [name, makePayload] of cases) await t.test(name, async () => {
    const events = [];
    const tab = makeTab({ indexedDB: new IDBFactory(), kind: 'inquiry', fetchImpl: (url, options) => url === '/api/orders.php'
      ? Promise.resolve({ ok: true, json: async () => makePayload(JSON.parse(options.body).requestId) })
      : configResponse() });
    tab.document.addEventListener('cm:analytics', event => events.push(event.detail));
    const form = tab.document.querySelector('.order-form');
    form.elements.comment.value = 'Проверка запроса';
    form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
    assert.ok(await waitFor(() => events.some(event => event.name === 'form_error' && event.params.reason === 'server_rejected')));
    assert.equal(events.filter(event => event.name === 'form_success').length, 0);
    await tick(); tab.dom.window.close();
  });
});

test('only a matching acknowledgement is counted once, while legacy receipts and new requests remain valid', async () => {
  const pending = [], events = [], submittedIds = [];
  const tab = makeTab({ indexedDB: new IDBFactory(), kind: 'inquiry', fetchImpl: (url, options) => url === '/api/orders.php'
    ? (submittedIds.push(JSON.parse(options.body).requestId), new Promise(resolve => pending.push(resolve)))
    : configResponse() });
  tab.document.addEventListener('cm:analytics', event => events.push(event.detail));
  const form = tab.document.querySelector('.order-form');
  form.elements.comment.value = 'Проверка запроса';
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.ok(await waitFor(() => pending.length === 1));
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.ok(await waitFor(() => pending.length === 2));
  assert.equal(submittedIds[0], submittedIds[1]);
  pending[0](await acceptedOrderResponse(submittedIds[0], { orderNumber: null }));
  pending[1](await acceptedOrderResponse(submittedIds[1], { orderNumber: null }));
  assert.ok(await waitFor(() => events.filter(event => event.name === 'form_success').length === 1));
  assert.match(form.querySelector('.form-status').textContent, /Старая заявка от/);
  assert.equal(JSON.stringify(events).includes(submittedIds[0]), false, 'request IDs stay out of analytics events');

  form.elements.comment.value = 'Следующий отдельный запрос';
  form.elements.comment.dispatchEvent(new tab.window.Event('input', { bubbles: true }));
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.ok(await waitFor(() => pending.length === 3));
  assert.notEqual(submittedIds[2], submittedIds[0]);
  pending[2](await acceptedOrderResponse(submittedIds[2]));
  assert.ok(await waitFor(() => events.filter(event => event.name === 'form_success').length === 2));
  await tick(); tab.dom.window.close();
});

test('disabled submission mode can save a request without requiring consent or posting it', async () => {
  const calls = [], tab = makeTab({ indexedDB: new IDBFactory(), kind: 'inquiry', fetchImpl: (url, options) => {
    calls.push(url);
    return Promise.resolve({ ok: true, json: async () => ({ submissionEnabled: false, consentVersion: '1' }) });
  } });
  const form = tab.document.querySelector('.order-form');
  assert.equal(form.noValidate, true);
  form.elements.comment.value = 'Part number unknown'; form.elements.consent.checked = false;
  form.querySelector('[type="submit"]').click();
  assert.ok(await waitFor(() => form.querySelector('.form-status').textContent.includes('сохранён в файл')));
  assert.deepEqual(calls, ['/api/config.php']);
  assert.equal(form.querySelector('[data-export]').hidden, false);
  await tick(); tab.dom.window.close();
});

test('aborted quantity update replays after reload only while its base cart revision still matches', async () => {
  const indexedDB = abortOneCartWrite(new IDBFactory());
  const first = makeTab({ indexedDB, seed: JSON.stringify([{ id: 'product-a', quantity: 1 }]) });
  assert.ok(await waitFor(() => /Part A/.test(first.document.querySelector('#cart-items').textContent)));
  assert.equal((await readCartRecord(indexedDB)).items[0].quantity, 1);
  indexedDB.abortNextWrite();
  await first.document.querySelector('[data-cart-open]').click();
  const quantity = first.document.querySelector('[data-quantity-input]');
  quantity.value = '3'; quantity.dispatchEvent(new first.window.Event('change', { bubbles: true }));
  assert.ok(await waitFor(() => indexedDB.abortCount === 1));
  const checkpoint = first.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint');
  assert.deepEqual(JSON.parse(checkpoint), { baseRevision: 0, quantities: { 'product-a': 3 } });
  assert.equal((await readCartRecord(indexedDB)).items[0].quantity, 1);
  first.dom.window.close();
  const reloaded = makeTab({ indexedDB, sessionSeed: checkpoint });
  assert.ok(await waitFor(() => reloaded.document.querySelector('[data-quantity-input]')?.value === '3'));
  assert.equal((await readCartRecord(indexedDB)).items[0].quantity, 3);
  assert.equal(reloaded.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint'), null);
  await tick(); reloaded.dom.window.close();

  const staleDb = new IDBFactory();
  await writeCartRecord(staleDb, { items: [{ id: 'product-a', quantity: 1 }], revision: 4 });
  const stale = makeTab({ indexedDB: staleDb, sessionSeed: JSON.stringify({ baseRevision: 3, quantities: { 'product-a': 3 } }) });
  assert.ok(await waitFor(() => stale.document.querySelector('[data-quantity-input]')?.value === '1'));
  assert.equal((await readCartRecord(staleDb)).items[0].quantity, 1);
  assert.equal(stale.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint'), null);
  await tick(); stale.dom.window.close();
});

test('committed cart submission clears quantity checkpoint without resurrecting items', async () => {
  const indexedDB = new IDBFactory();
  const tab = makeTab({ indexedDB, seed: JSON.stringify([{ id: 'product-a', quantity: 1 }]), fetchImpl: (url, options) => url === '/api/orders.php'
    ? acceptedOrderResponse(JSON.parse(options.body).requestId)
    : configResponse() });
  assert.ok(await waitFor(() => /Part A/.test(tab.document.querySelector('#cart-items').textContent)));
  await tab.document.querySelector('[data-cart-open]').click();
  const quantity = tab.document.querySelector('[data-quantity-input]');
  quantity.value = '3'; quantity.dispatchEvent(new tab.window.Event('change', { bubbles: true }));
  assert.deepEqual(JSON.parse(tab.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint')), { baseRevision: 0, quantities: { 'product-a': 3 } });
  assert.ok(await waitForCartRecord(indexedDB, record => record.items[0]?.quantity === 3));
  assert.equal(tab.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint'), null);
  const form = tab.document.querySelector('.order-form');
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.ok(await waitFor(() => tab.document.querySelector('[data-cart-count]').textContent === '0'));
  const reloaded = makeTab({ indexedDB, sessionSeed: tab.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint') });
  assert.ok(await waitFor(() => reloaded.document.querySelector('[data-cart-count]').textContent === '0'));
  assert.equal((await readCartRecord(indexedDB)).items.length, 0);
  assert.equal(reloaded.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint'), null);
  await tick(); tab.dom.window.close(); reloaded.dom.window.close();
});

test('successful submission preserves a newer aborted quantity edit made while POST is pending', async () => {
  const indexedDB = abortOneCartWrite(new IDBFactory()); let resolveOrder, submittedRequestId;
  const tab = makeTab({ indexedDB, seed: JSON.stringify([{ id: 'product-a', quantity: 1 }]), fetchImpl: (url, options) => url === '/api/orders.php'
    ? (submittedRequestId = JSON.parse(options.body).requestId, new Promise(resolve => { resolveOrder = resolve; }))
    : configResponse() });
  assert.ok(await waitFor(() => /Part A/.test(tab.document.querySelector('#cart-items').textContent)));
  const form = tab.document.querySelector('.order-form');
  form.dispatchEvent(new tab.window.Event('submit', { bubbles: true, cancelable: true }));
  assert.ok(await waitFor(() => typeof resolveOrder === 'function'));
  indexedDB.abortNextWrite();
  await tab.document.querySelector('[data-cart-open]').click();
  const quantity = tab.document.querySelector('[data-quantity-input]');
  quantity.value = '3'; quantity.dispatchEvent(new tab.window.Event('change', { bubbles: true }));
  assert.ok(await waitFor(() => indexedDB.abortCount === 1));
  const checkpoint = tab.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint');
  assert.deepEqual(JSON.parse(checkpoint), { baseRevision: 0, quantities: { 'product-a': 3 } });
  resolveOrder(await acceptedOrderResponse(submittedRequestId));
  assert.ok(await waitFor(() => form.querySelector('.form-status').textContent.includes('Accepted')));
  assert.equal(tab.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint'), checkpoint);
  tab.dom.window.close();
  const reloaded = makeTab({ indexedDB, sessionSeed: checkpoint });
  assert.ok(await waitFor(() => reloaded.document.querySelector('[data-quantity-input]')?.value === '3'));
  assert.equal((await readCartRecord(indexedDB)).items[0].quantity, 3);
  assert.equal(reloaded.window.sessionStorage.getItem('cm-techno-cart-quantity-checkpoint'), null);
  await tick(); reloaded.dom.window.close();
});
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
  resolveOrder(await acceptedOrderResponse(payload.requestId));
  await waitFor(() => form.querySelector('.form-status').textContent.includes('Заявка № 42 от 07.10.2026'));
  assert.match(form.querySelector('.form-status').textContent, /Заявка № 42 от 07\.10\.2026/);
  await tick();
  tab.dom.window.close();
});

test('successful submit preserves cart and form edits made while the request is pending', async () => {
  const indexedDB = new IDBFactory();
  let resolveOrder, submittedRequestId;
  const fetchImpl = (url, options) => url === '/api/orders.php'
    ? (submittedRequestId = JSON.parse(options.body).requestId, new Promise(resolve => { resolveOrder = resolve; }))
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
  resolveOrder(await acceptedOrderResponse(submittedRequestId));
  await waitFor(() => tab.document.querySelector('.form-status').textContent.includes('Accepted'));
  assert.doesNotMatch(tab.document.querySelector('.form-status').textContent, /Старая заявка от|request-123/);
  assert.match(document.querySelector('#cart-items').textContent, /Part A/);
  assert.match(document.querySelector('#cart-items').textContent, /Part B/);
  assert.equal(form.elements.name.value, 'Edited while sending');
  await tick();
  tab.dom.window.close();
});

test('clear uses the submitted revision and does not erase an ABA remove-and-readd', async () => {
  const indexedDB = new IDBFactory();
  let resolveOrder, submittedRequestId;
  const fetchImpl = (url, options) => url === '/api/orders.php'
    ? (submittedRequestId = JSON.parse(options.body).requestId, new Promise(resolve => { resolveOrder = resolve; }))
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
  resolveOrder(await acceptedOrderResponse(submittedRequestId));
  await waitFor(() => form.querySelector('.form-status').textContent.includes('Accepted'));
  assert.doesNotMatch(form.querySelector('.form-status').textContent, /Старая заявка от|request-123/);
  assert.match(tab.document.querySelector('#cart-items').textContent, /Part A/);
  await tick();
  tab.dom.window.close();
});

test('an empty committed cart does not resurrect legacy items and remains usable without IndexedDB', async () => {
  const indexedDB = new IDBFactory();
  const fetchImpl = (url, options) => url === '/api/orders.php'
    ? acceptedOrderResponse(JSON.parse(options.body).requestId)
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
