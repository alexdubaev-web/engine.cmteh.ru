const CONSENT_KEY = 'cmteh.analytics-consent.v1';
const CONSENT_VERSION = 1;
const MAX_AGE = 90 * 24 * 60 * 60 * 1000;
const COUNTER_ID = 113475902;

export function createAnalyticsConsent({ window: win, document: doc, storage, now = Date.now }) {
  const panel = doc.querySelector('[data-analytics-panel]');
  if (!panel || win.location.hostname !== 'engine.cmteh.ru') return { enabled: false };
  const allowButton = panel.querySelector('[data-analytics-allow]');
  const denyButton = panel.querySelector('[data-analytics-deny]');
  const status = panel.querySelector('[data-analytics-status]');
  let script = null;
  let enabled = false;
  let closed = false;
  let loadGeneration = 0;

  const readRecord = () => {
    try {
      const raw = storage.getItem(CONSENT_KEY);
      const value = JSON.parse(raw);
      if (value?.version !== CONSENT_VERSION || !['accepted', 'rejected'].includes(value.decision) ||
          !Number.isFinite(value.savedAt) || now() - value.savedAt < 0 || now() - value.savedAt >= MAX_AGE) return null;
      return { raw, decision: value.decision };
    } catch { return null; }
  };
  const getDecision = () => readRecord()?.decision || null;
  const setDecision = decision => {
    try {
      const raw = JSON.stringify({ version: CONSENT_VERSION, decision, savedAt: now() });
      storage.setItem(CONSENT_KEY, raw);
      return storage.getItem(CONSENT_KEY) === raw;
    }
    catch { return false; }
  };
  const removeDecision = () => { try { storage.removeItem(CONSENT_KEY); } catch {} };
  const verifyStoredAcceptance = () => {
    const record = readRecord();
    if (record?.decision !== 'accepted') return false;
    try {
      storage.setItem(CONSENT_KEY, record.raw);
      if (storage.getItem(CONSENT_KEY) !== record.raw) throw Error('Consent could not be verified');
      return true;
    } catch {
      removeDecision();
      return false;
    }
  };
  const show = () => { panel.hidden = false; allowButton.focus(); };
  const hide = () => { panel.hidden = true; };
  const validConsent = () => !closed && enabled && getDecision() === 'accepted';
  win.ym = win.ym || function () { (win.ym.a = win.ym.a || []).push(arguments); };

  const stop = () => {
    loadGeneration += 1;
    closed = true;
    enabled = false;
    if (script?.parentNode) script.parentNode.removeChild(script);
    script = null;
    if (typeof win.ym === 'function') win.ym(COUNTER_ID, 'destruct');
  };
  const recheckConsent = () => {
    if (getDecision() === 'accepted') return;
    stop();
    if (getDecision() === null) show();
    else hide();
  };
  win.addEventListener('storage', event => {
    if (event.key !== CONSENT_KEY && event.key !== null) return;
    const record = readRecord();
    if (record?.decision === 'accepted') {
      closed = false;
      enabled = true;
      hide();
      start();
    } else recheckConsent();
  });
  win.addEventListener('focus', recheckConsent);
  doc.addEventListener('visibilitychange', () => { if (!doc.hidden) recheckConsent(); });
  const revoke = () => {
    stop();
    if (!setDecision('rejected')) {
      removeDecision();
      status.textContent = 'Аналитика выключена в этой вкладке, но браузер не смог сохранить отказ. Проверьте настройки хранилища и повторите отказ.';
      show();
      return false;
    }
    status.textContent = '';
    hide();
    return true;
  };
  const start = () => {
    if (!validConsent() || script) return;
    const generation = ++loadGeneration;
    script = doc.createElement('script');
    script.async = true;
    script.src = `https://mc.yandex.ru/metrika/tag.js?id=${COUNTER_ID}`;
    script.referrerPolicy = 'no-referrer';
    script.onload = () => {
      if (generation !== loadGeneration) return;
      if (!validConsent()) { stop(); return; }
      if (typeof win.ym !== 'function') { stop(); return; }
      const cleanReferrer = (() => { try { const url = new URL(doc.referrer); return url.origin + url.pathname; } catch { return ''; } })();
      win.ym(COUNTER_ID, 'init', {
        ssr: true, webvisor: true, clickmap: true, ecommerce: 'dataLayer',
        accurateTrackBounce: true, trackLinks: true,
        url: `${win.location.origin}${win.location.pathname}`,
        referrer: cleanReferrer
      });
    };
    doc.head.appendChild(script);
  };

  allowButton.addEventListener('click', () => {
    if (!setDecision('accepted')) { status.textContent = 'Браузер не позволяет сохранить выбор. Аналитика останется выключенной.'; return; }
    status.textContent = '';
    closed = false;
    enabled = true;
    hide();
    start();
  });
  denyButton.addEventListener('click', () => {
    revoke();
  });
  doc.querySelectorAll('[data-analytics-preferences]').forEach(button => button.addEventListener('click', show));
  win.addEventListener('keydown', event => { if (event.key === 'Escape' && !panel.hidden) hide(); });

  const decision = getDecision();
  if (decision === 'accepted' && verifyStoredAcceptance()) { enabled = true; start(); }
  else if (decision === 'accepted') {
    status.textContent = 'Не удалось подтвердить сохранённое разрешение. Аналитика останется выключенной.';
    show();
  } else if (decision !== 'rejected') show();
  return { enabled: decision === 'accepted' && enabled, revoke };
}

try { createAnalyticsConsent({ window, document, storage: window.localStorage }); } catch {}
