// Vibenote side panel logic.
// Talks to the native messaging bridge (~/.vibenote/bin/vibenote-bridge.py).

const NATIVE_HOST = 'com.vibenote.bridge';

const els = {
  // Capture tab
  title: document.getElementById('title'),
  url: document.getElementById('url'),
  favicon: document.getElementById('favicon'),
  thread: document.getElementById('thread'),
  threadHint: document.getElementById('thread-hint'),
  content: document.getElementById('content'),
  save: document.getElementById('save'),
  // Notes tab
  askThread: document.getElementById('ask-thread'),
  threadScopeSummary: document.getElementById('thread-scope-summary'),
  askLabel: document.getElementById('ask-label'),
  question: document.getElementById('question'),
  askSubmit: document.getElementById('ask-submit'),
  quickQueries: document.querySelectorAll('.chip'),
  answerEmpty: document.getElementById('answer-empty'),
  answerLoading: document.getElementById('answer-loading'),
  answerContent: document.getElementById('answer-content'),
  answerMeta: document.getElementById('answer-meta'),
  answerBody: document.getElementById('answer-body'),
  answerError: document.getElementById('answer-error'),
  answerErrorText: document.getElementById('answer-error-text'),
  // Pages
  pageCapture: document.getElementById('page-capture'),
  pageNotes: document.getElementById('page-notes'),
  tabs: document.querySelectorAll('.tab'),
  // Global
  status: document.getElementById('status'),
  statusText: document.querySelector('.status-text'),
  configIndicator: document.getElementById('config-indicator'),
};

let currentDraftUrl = '';
let cachedThreads = [];
let activeTab = 'capture';
let currentAnswerState = 'empty'; // 'empty' | 'loading' | 'content' | 'error'
let vaultPath = '';

// ---------- Native messaging ----------

function callBridge(payload, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        reject(new Error('Bridge call timed out'));
      }
    }, timeoutMs);
    try {
      chrome.runtime.sendNativeMessage(NATIVE_HOST, payload, (response) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        resolve(response);
      });
    } catch (err) {
      settled = true;
      clearTimeout(timer);
      reject(err);
    }
  });
}

// ---------- Tab switching ----------

function switchTab(name) {
  activeTab = name;
  els.tabs.forEach((t) => {
    const isActive = t.dataset.tab === name;
    t.classList.toggle('active', isActive);
    t.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });
  els.pageCapture.hidden = name !== 'capture';
  els.pageNotes.hidden = name !== 'notes';

  // Focus the right input for the active tab.
  if (name === 'capture') {
    els.content.focus();
  } else if (name === 'notes') {
    els.question.focus();
  }
}

els.tabs.forEach((tab) => {
  tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

// ---------- UI helpers ----------

function setStatus(text, cls) {
  els.statusText.textContent = text;
  els.status.className = 'status' + (cls ? ' ' + cls : '');
}

function setConfigIndicator(path) {
  if (!path) {
    els.configIndicator.textContent = '';
    return;
  }
  // Shorten the home path for display.
  const display = path.replace(/^\/Users\/[^/]+/, '~');
  els.configIndicator.textContent = display;
  els.configIndicator.title = `Claude config: ${path}`;
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
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${u.hostname}&sz=32`;
    els.favicon.src = faviconUrl;
    els.favicon.onerror = () => els.favicon.removeAttribute('src');
  } catch {
    els.favicon.removeAttribute('src');
  }
}

function populateThreads(threads) {
  cachedThreads = threads;

  // Capture dropdown: "auto-classify" default + each thread
  while (els.thread.options.length > 1) {
    els.thread.remove(1);
  }
  if (threads.length === 0) {
    els.threadHint.textContent = 'No threads yet — your first capture will create one.';
  } else {
    els.threadHint.textContent = '';
    for (const t of threads) {
      const opt = document.createElement('option');
      opt.value = t.slug;
      const summary = (t.summary || '').trim();
      const short = summary.length > 50 ? summary.slice(0, 47) + '…' : summary;
      opt.textContent = short ? `${t.slug}  ·  ${short}` : t.slug;
      els.thread.appendChild(opt);
    }
  }

  // Notes tab thread picker: each thread (sorted by updated desc, already the
  // order the index returns), then "all threads" as a non-default escape hatch.
  populateAskThread(threads);
}

function populateAskThread(threads) {
  els.askThread.innerHTML = '';

  if (threads.length === 0) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = 'No threads yet — capture something first';
    opt.disabled = true;
    els.askThread.appendChild(opt);
    els.threadScopeSummary.textContent = '';
    return;
  }

  // Threads sorted by updated desc (the index already returns them this way)
  for (const t of threads) {
    const opt = document.createElement('option');
    opt.value = t.slug;
    opt.textContent = t.slug;
    opt.dataset.summary = t.summary || '';
    opt.dataset.entries = t.entries || '';
    opt.dataset.updated = t.updated || '';
    els.askThread.appendChild(opt);
  }

  // "All threads" escape hatch at the bottom
  const divider = document.createElement('option');
  divider.disabled = true;
  divider.textContent = '──────────';
  els.askThread.appendChild(divider);

  const allOpt = document.createElement('option');
  allOpt.value = '__all__';
  allOpt.textContent = '— All threads —';
  els.askThread.appendChild(allOpt);

  // Default to most-recently-updated (first in the list)
  els.askThread.value = threads[0].slug;
  updateAskScope();
}

function updateAskScope() {
  const selected = els.askThread.value;
  const option = els.askThread.selectedOptions[0];

  if (selected === '__all__') {
    els.askLabel.textContent = 'Ask across all threads';
    els.question.placeholder = 'What do you want to know across everything?';
    els.threadScopeSummary.textContent = `Searching all ${cachedThreads.length} threads.`;
  } else if (selected && option) {
    els.askLabel.textContent = 'Ask about this thread';
    els.question.placeholder = `What do you want to know about ${selected}?`;
    const summary = option.dataset.summary || '';
    const entries = option.dataset.entries || '';
    const updated = option.dataset.updated || '';
    const entriesPart = entries ? `${entries} entr${entries === '1' ? 'y' : 'ies'}` : '';
    const updatedPart = updated ? `updated ${updated}` : '';
    const meta = [entriesPart, updatedPart].filter(Boolean).join(' · ');
    els.threadScopeSummary.textContent = summary
      ? (meta ? `${summary}\n${meta}` : summary)
      : meta;
  } else {
    els.askLabel.textContent = 'Ask your notes';
    els.question.placeholder = 'What do you want to know?';
    els.threadScopeSummary.textContent = '';
  }

  // Clear any existing answer since it was for a different scope.
  if (currentAnswerState === 'content' || currentAnswerState === 'error') {
    setAnswerState('empty');
  }
}

// ---------- Tab state for capture view ----------

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

async function loadPing() {
  try {
    const response = await callBridge({ op: 'ping' });
    if (response && response.ok) {
      vaultPath = response.vault || '';
      if (response.claude_config_dir) {
        setConfigIndicator(response.claude_config_dir);
      }
    }
  } catch (err) {
    console.error('Vibenote: ping failed', err);
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

// ---------- Capture action ----------

async function handleCapture() {
  const content = els.content.value.trim();
  const title = els.title.textContent.trim();
  const url = els.url.dataset.fullUrl || '';

  if (!content && !title && !url) {
    setStatus('Nothing to capture', 'error');
    setTimeout(() => setStatus('Connected', 'connected'), 2000);
    return;
  }

  const isBookmark = !content;
  const isAutoClassify = !els.thread.value;
  els.save.disabled = true;

  // Auto-classify uses the LLM and takes 5-10s — show a distinct status.
  if (isAutoClassify && !isBookmark) {
    setStatus('Classifying & capturing…', 'connecting');
    els.save.querySelector('.btn-label').textContent = 'Classifying…';
  } else {
    setStatus(isBookmark ? 'Bookmarking…' : 'Capturing…', 'connecting');
  }

  try {
    const response = await callBridge({
      op: 'capture',
      title,
      url,
      content,
      thread: els.thread.value || undefined,
    }, 60000); // longer timeout for LLM classification

    if (response && response.ok) {
      const threadList = (response.threads || [response.thread]).join(', ');
      const hasNew = (response.created_new || []).length > 0;
      const newBadge = hasNew ? ' (new)' : '';
      const verb = isBookmark ? 'Bookmarked' : 'Captured';
      setStatus(`${verb} to ${threadList}${newBadge}`, 'success');

      els.save.classList.add('success');
      els.save.querySelector('.btn-label').textContent = verb;
      setTimeout(() => {
        els.save.classList.remove('success');
        els.save.querySelector('.btn-label').textContent = 'Capture';
      }, 1800);

      els.content.value = '';
      await clearDraft();

      if (hasNew) {
        loadThreads();
      }
      // Keep the success status visible longer so user can read which threads.
      setTimeout(() => setStatus('Connected', 'connected'), 4000);
    } else {
      setStatus(response?.error || 'Capture failed', 'error');
    }
  } catch (err) {
    setStatus('Bridge error: ' + err.message, 'error');
  } finally {
    els.save.disabled = false;
  }
}

// ---------- Ask action (Notes tab) ----------

function setAnswerState(state) {
  currentAnswerState = state;
  els.answerEmpty.hidden = state !== 'empty';
  els.answerLoading.hidden = state !== 'loading';
  els.answerContent.hidden = state !== 'content';
  els.answerError.hidden = state !== 'error';
}

// Minimal markdown renderer — just the subset that claude typically emits.
function renderMarkdown(text) {
  // Escape HTML first, then apply markdown-like transforms.
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code spans (`foo`) — do this before bold/italic so backticks don't get eaten.
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold (**foo**) — before italic
  html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');

  // Italic (*foo* or _foo_)
  html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>');

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Citations: (from slug) → clickable chip
  html = html.replace(
    /\(from ([a-z0-9][a-z0-9-]*)\)/g,
    '<a class="citation" data-slug="$1" href="#">$1</a>'
  );

  // Lists — group consecutive lines starting with "- " or "* " into <ul>
  const lines = html.split('\n');
  const out = [];
  let inList = false;
  for (const line of lines) {
    const listMatch = line.match(/^[-*] (.+)$/);
    if (listMatch) {
      if (!inList) {
        out.push('<ul>');
        inList = true;
      }
      out.push(`<li>${listMatch[1]}</li>`);
    } else {
      if (inList) {
        out.push('</ul>');
        inList = false;
      }
      out.push(line);
    }
  }
  if (inList) out.push('</ul>');
  html = out.join('\n');

  // Paragraphs — wrap non-tag lines separated by blank lines.
  const blocks = html.split(/\n\n+/);
  html = blocks
    .map((block) => {
      const trimmed = block.trim();
      if (!trimmed) return '';
      if (trimmed.startsWith('<h') || trimmed.startsWith('<ul') || trimmed.startsWith('<ol')) {
        return trimmed;
      }
      return `<p>${trimmed.replace(/\n/g, ' ')}</p>`;
    })
    .join('\n');

  return html;
}

function attachCitationHandlers() {
  const citations = els.answerBody.querySelectorAll('.citation');
  citations.forEach((el) => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const slug = el.dataset.slug;
      if (!slug || !vaultPath) return;
      // Open the thread file in Obsidian via its URL scheme.
      const path = `${vaultPath}/threads/${slug}.md`;
      const obsidianUrl = `obsidian://open?path=${encodeURIComponent(path)}`;
      window.open(obsidianUrl, '_blank');
    });
  });
}

// Prompt templates for quick-query buttons. Two versions each: thread-scoped
// (when a specific thread is selected) and corpus-wide (when "All threads" is).
const QUICK_QUERY_PROMPTS = {
  'where-am-i': {
    thread: 'Summarize where I currently am with this thread. What are the key decisions I\'ve made, the current direction, and what\'s in flight? Keep it concise.',
    all: 'Give me a quick state of my whole vault: which threads are active, what\'s the latest thinking in each, and where am I overall?',
  },
  'open-questions': {
    thread: 'What are the open questions in this thread? List them with the context I have around each.',
    all: 'What are all my open questions across every thread? Group by thread.',
  },
  'next-steps': {
    thread: 'Based on everything in this thread, what should I work on next? Suggest specific next actions grounded in my notes.',
    all: 'Based on my recent captures and open questions across all threads, what should I work on next? Suggest specific next actions.',
  },
};

function getActiveScope() {
  const selected = els.askThread.value;
  if (!selected || selected === '__all__') return null; // null = corpus-wide
  return selected;
}

async function handleAsk(questionOverride) {
  const question = (questionOverride || els.question.value).trim();
  if (!question) {
    els.question.focus();
    return;
  }

  if (questionOverride) {
    els.question.value = questionOverride;
  }

  const scopeSlug = getActiveScope();

  setAnswerState('loading');
  els.askSubmit.disabled = true;
  els.quickQueries.forEach((b) => (b.disabled = true));

  try {
    const payload = { op: 'ask', question };
    if (scopeSlug) payload.thread = scopeSlug;

    const response = await callBridge(payload, 60000);

    if (response && response.ok) {
      const latencySec = (response.latency_ms / 1000).toFixed(1);
      const scopeLabel = response.scope || 'unknown';
      els.answerMeta.textContent = `${latencySec}s · scoped to ${scopeLabel}`;
      els.answerBody.innerHTML = renderMarkdown(response.answer);
      attachCitationHandlers();
      setAnswerState('content');
    } else {
      els.answerErrorText.textContent = response?.error || 'Ask failed';
      setAnswerState('error');
    }
  } catch (err) {
    els.answerErrorText.textContent = 'Bridge error: ' + err.message;
    setAnswerState('error');
  } finally {
    els.askSubmit.disabled = false;
    els.quickQueries.forEach((b) => (b.disabled = false));
  }
}

function handleQuickQuery(btn) {
  const type = btn.dataset.queryType;
  const prompts = QUICK_QUERY_PROMPTS[type];
  if (!prompts) return;
  const scopeSlug = getActiveScope();
  const prompt = scopeSlug ? prompts.thread : prompts.all;
  handleAsk(prompt);
}

els.askSubmit.addEventListener('click', () => handleAsk());
els.askThread.addEventListener('change', updateAskScope);
els.quickQueries.forEach((btn) => {
  btn.addEventListener('click', () => handleQuickQuery(btn));
});

// ---------- Event wiring ----------

els.save.addEventListener('click', handleCapture);

document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    if (activeTab === 'capture') {
      handleCapture();
    } else if (activeTab === 'notes') {
      handleAsk();
    }
  }
});

// Autosave draft on content change (debounced).
let draftTimer = null;
els.content.addEventListener('input', () => {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(saveDraft, 500);
});
els.thread.addEventListener('change', saveDraft);

// Contenteditable title behavior.
els.title.addEventListener('input', () => {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(saveDraft, 500);
});
els.title.addEventListener('paste', (e) => {
  e.preventDefault();
  const text = e.clipboardData.getData('text/plain');
  document.execCommand('insertText', false, text);
});
els.title.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    els.content.focus();
  }
});

// ---------- Tab change listeners (browser tab, not UI tab) ----------

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
  await loadPing();
  await loadThreads();
  await restoreDraft();
  els.content.focus();
})();
