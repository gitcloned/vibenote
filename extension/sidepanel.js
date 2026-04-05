// Vibenote side panel logic.
// Talks to the native messaging bridge (~/.vibenote/bin/vibenote-bridge.py).

const NATIVE_HOST = 'com.vibenote.bridge';

const els = {
  title: document.getElementById('title'),
  url: document.getElementById('url'),
  favicon: document.getElementById('favicon'),
  thread: document.getElementById('thread'),
  threadHint: document.getElementById('thread-hint'),
  content: document.getElementById('content'),
  save: document.getElementById('save'),
  status: document.getElementById('status'),
  statusText: document.querySelector('.status-text'),
};

// Track which URL the current draft belongs to, so we can save it under the
// right key when the user switches tabs.
let currentDraftUrl = '';
let cachedThreads = [];

// ---------- Native messaging ----------

function callBridge(payload) {
  return new Promise((resolve, reject) => {
    try {
      chrome.runtime.sendNativeMessage(NATIVE_HOST, payload, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        resolve(response);
      });
    } catch (err) {
      reject(err);
    }
  });
}

// ---------- UI helpers ----------

function setStatus(text, cls) {
  els.statusText.textContent = text;
  els.status.className = 'status' + (cls ? ' ' + cls : '');
}

function formatUrl(url) {
  if (!url) return '';
  try {
    const u = new URL(url);
    const host = u.hostname.replace(/^www\./, '');
    const path = u.pathname + u.search;
    if (path === '/' || path === '') return host;
    if (path.length + host.length <= 60) return host + path;
    return host + '…' + path.slice(-Math.max(20, 60 - host.length));
  } catch {
    return url;
  }
}

function setFavicon(url) {
  if (!url) {
    els.favicon.removeAttribute('src');
    return;
  }
  try {
    const u = new URL(url);
    // Chrome's built-in favicon service (works for any visited origin).
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${u.hostname}&sz=32`;
    els.favicon.src = faviconUrl;
    els.favicon.onerror = () => els.favicon.removeAttribute('src');
  } catch {
    els.favicon.removeAttribute('src');
  }
}

function populateThreads(threads) {
  cachedThreads = threads;
  // Clear all options except the "auto-classify" placeholder (index 0).
  while (els.thread.options.length > 1) {
    els.thread.remove(1);
  }
  if (threads.length === 0) {
    els.threadHint.textContent = 'No threads yet — your first save will create one.';
    return;
  }
  els.threadHint.textContent = '';
  for (const t of threads) {
    const opt = document.createElement('option');
    opt.value = t.slug;
    // Native <select> options can't show two lines, so we flatten with a separator.
    // Keep it short — long summaries get truncated anyway.
    const summary = (t.summary || '').trim();
    const short = summary.length > 50 ? summary.slice(0, 47) + '…' : summary;
    opt.textContent = short ? `${t.slug}  ·  ${short}` : t.slug;
    els.thread.appendChild(opt);
  }
}

// ---------- Tab state ----------

async function loadCurrentTab() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      els.title.textContent = tab.title || '';
      els.url.textContent = formatUrl(tab.url || '');
      els.url.title = tab.url || '';
      els.url.dataset.fullUrl = tab.url || '';
      setFavicon(tab.url);
      return tab;
    }
  } catch (err) {
    console.error('Vibenote: failed to read active tab', err);
  }
  return null;
}

// Immediately persist the current draft under the URL it belongs to.
async function flushDraft() {
  if (!currentDraftUrl) return;
  try {
    const key = `draft:${currentDraftUrl}`;
    if (els.content.value.trim()) {
      await chrome.storage.local.set({
        [key]: {
          content: els.content.value,
          thread: els.thread.value,
          savedAt: Date.now(),
        },
      });
    } else {
      await chrome.storage.local.remove(key);
    }
  } catch (err) {
    console.error('Vibenote: failed to flush draft', err);
  }
}

async function refreshForCurrentTab() {
  clearTimeout(draftTimer);
  await flushDraft();

  els.content.value = '';
  els.thread.value = '';

  await loadCurrentTab();
  currentDraftUrl = els.url.dataset.fullUrl || '';
  await restoreDraft();
}

async function loadThreads() {
  try {
    const response = await callBridge({ op: 'list-threads' });
    if (response && response.ok) {
      populateThreads(response.threads || []);
      setStatus('Connected', 'connected');
    } else {
      setStatus('Bridge error', 'error');
      console.error('Vibenote: list-threads failed', response);
    }
  } catch (err) {
    setStatus('Not connected', 'error');
    console.error('Vibenote: bridge unreachable', err);
  }
}

// ---------- Drafts ----------

async function restoreDraft() {
  if (!currentDraftUrl) return;
  try {
    const key = `draft:${currentDraftUrl}`;
    const stored = await chrome.storage.local.get(key);
    const draft = stored[key];
    if (draft) {
      els.content.value = draft.content || '';
      if (draft.thread) {
        els.thread.value = draft.thread;
      }
    }
  } catch (err) {
    console.error('Vibenote: failed to restore draft', err);
  }
}

async function saveDraft() {
  if (!currentDraftUrl) return;
  try {
    const key = `draft:${currentDraftUrl}`;
    if (els.content.value.trim()) {
      await chrome.storage.local.set({
        [key]: {
          content: els.content.value,
          thread: els.thread.value,
          savedAt: Date.now(),
        },
      });
    } else {
      await chrome.storage.local.remove(key);
    }
  } catch (err) {
    console.error('Vibenote: failed to save draft', err);
  }
}

async function clearDraft() {
  if (!currentDraftUrl) return;
  try {
    const key = `draft:${currentDraftUrl}`;
    await chrome.storage.local.remove(key);
  } catch (err) {
    console.error('Vibenote: failed to clear draft', err);
  }
}

// ---------- Save action ----------

async function handleCapture() {
  const content = els.content.value.trim();
  const title = els.title.textContent.trim();
  const url = els.url.dataset.fullUrl || '';

  // Require at least something to identify what we're capturing.
  // Empty body is allowed (bookmark mode) as long as we have a URL or title.
  if (!content && !title && !url) {
    setStatus('Nothing to capture', 'error');
    setTimeout(() => setStatus('Connected', 'connected'), 2000);
    return;
  }

  const isBookmark = !content;
  els.save.disabled = true;
  setStatus(isBookmark ? 'Bookmarking…' : 'Capturing…', 'connecting');

  try {
    const response = await callBridge({
      op: 'capture',
      title,
      url,
      content,
      thread: els.thread.value || undefined,
    });

    if (response && response.ok) {
      const newBadge = response.created_new ? ' (new thread)' : '';
      const verb = isBookmark ? 'Bookmarked' : 'Captured';
      setStatus(`${verb} to ${response.thread}${newBadge}`, 'success');

      // Brief success state on the button itself.
      els.save.classList.add('success');
      els.save.querySelector('.btn-label').textContent = isBookmark ? 'Bookmarked' : 'Captured';
      setTimeout(() => {
        els.save.classList.remove('success');
        els.save.querySelector('.btn-label').textContent = 'Capture';
      }, 1400);

      els.content.value = '';
      await clearDraft();

      if (response.created_new) {
        loadThreads();
      }
      setTimeout(() => setStatus('Connected', 'connected'), 2500);
    } else {
      setStatus(response?.error || 'Capture failed', 'error');
    }
  } catch (err) {
    setStatus('Bridge error: ' + err.message, 'error');
  } finally {
    els.save.disabled = false;
  }
}

// ---------- Event wiring ----------

els.save.addEventListener('click', handleCapture);

document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    handleCapture();
  }
});

// Autosave draft on content change (debounced).
let draftTimer = null;
els.content.addEventListener('input', () => {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(saveDraft, 500);
});
els.thread.addEventListener('change', saveDraft);

// Contenteditable title: save draft when edited (still uses the current URL).
els.title.addEventListener('input', () => {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(saveDraft, 500);
});
// Prevent contenteditable from accepting rich HTML on paste.
els.title.addEventListener('paste', (e) => {
  e.preventDefault();
  const text = e.clipboardData.getData('text/plain');
  document.execCommand('insertText', false, text);
});
// Enter in the title jumps focus to the textarea instead of inserting a newline.
els.title.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    els.content.focus();
  }
});

// ---------- Tab change listeners ----------

chrome.tabs.onActivated.addListener(async () => {
  await refreshForCurrentTab();
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (!changeInfo.url) return;
  if (!tab.active) return;
  await refreshForCurrentTab();
});

// ---------- Boot ----------

(async () => {
  setStatus('Connecting…', 'connecting');
  await loadCurrentTab();
  currentDraftUrl = els.url.dataset.fullUrl || '';
  await loadThreads();
  await restoreDraft();
  els.content.focus();
})();
