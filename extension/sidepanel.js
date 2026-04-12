// Vibenote side panel — capture + chat-based notes Q&A.

const NATIVE_HOST = 'com.vibenote.bridge';

// ---------- SVG Icons (Lucide-style, inline) ----------

const ICONS = {
  like: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"/><path d="M15 5.88L14 10h5.83a2 2 0 011.92 2.56l-2.33 8A2 2 0 0117.5 22H4a2 2 0 01-2-2v-8a2 2 0 012-2h2.76a2 2 0 001.79-1.11L12 2h0a3.13 3.13 0 013 3.88z"/></svg>',
  comment: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>',
  retry: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/></svg>',
  share: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
  copy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',
  more: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>',
  task: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  deeper: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>',
};

// ---------- DOM refs ----------

const els = {
  // Capture tab
  title: document.getElementById('title'),
  url: document.getElementById('url'),
  favicon: document.getElementById('favicon'),
  thread: document.getElementById('thread'),
  threadHint: document.getElementById('thread-hint'),
  content: document.getElementById('content'),
  save: document.getElementById('save'),
  // Notes tab — chat
  askThread: document.getElementById('ask-thread'),
  chatMessages: document.getElementById('chat-messages'),
  chatEmpty: document.getElementById('chat-empty'),
  question: document.getElementById('question'),
  askSubmit: document.getElementById('ask-submit'),
  chatChips: document.querySelectorAll('.chat-chips .chip'),
  // Pages
  pageCapture: document.getElementById('page-capture'),
  pageNotes: document.getElementById('page-notes'),
  tabs: document.querySelectorAll('.tab'),
  // Global
  status: document.getElementById('status'),
  statusText: document.querySelector('.status-text'),
  configIndicator: document.getElementById('config-indicator'),
};

// ---------- State ----------

let currentDraftUrl = '';
let cachedThreads = [];
let cachedConcepts = [];
let activeTab = 'capture';
let vaultPath = '';
let chatHistory = []; // {role, content, rawContent, queryType?, items?}
let lastUserQuery = '';

// ---------- Native messaging ----------

function callBridge(payload, timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (!settled) { settled = true; reject(new Error('Bridge call timed out')); }
    }, timeoutMs);
    try {
      chrome.runtime.sendNativeMessage(NATIVE_HOST, payload, (response) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        if (chrome.runtime.lastError) { reject(new Error(chrome.runtime.lastError.message)); return; }
        resolve(response);
      });
    } catch (err) { settled = true; clearTimeout(timer); reject(err); }
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
  if (name === 'notes') els.question.focus();
  else els.content.focus();
}

els.tabs.forEach((tab) => tab.addEventListener('click', () => switchTab(tab.dataset.tab)));

// ---------- UI helpers ----------

function setStatus(text, cls) {
  els.statusText.textContent = text;
  els.status.className = 'status' + (cls ? ' ' + cls : '');
}

function setConfigIndicator(path) {
  if (!path) { els.configIndicator.textContent = ''; return; }
  els.configIndicator.textContent = path.replace(/^\/Users\/[^/]+/, '~');
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
  } catch { return url; }
}

function setFavicon(url) {
  if (!url) { els.favicon.removeAttribute('src'); return; }
  try {
    const u = new URL(url);
    els.favicon.src = `https://www.google.com/s2/favicons?domain=${u.hostname}&sz=32`;
    els.favicon.onerror = () => els.favicon.removeAttribute('src');
  } catch { els.favicon.removeAttribute('src'); }
}

// ---------- Thread / concept dropdowns ----------

function populateThreads(threads) {
  cachedThreads = threads;
  // Capture dropdown
  while (els.thread.options.length > 1) els.thread.remove(1);
  if (threads.length === 0) {
    els.threadHint.textContent = 'No threads yet — your first capture will create one.';
  } else {
    els.threadHint.textContent = '';
    for (const t of threads) {
      const opt = document.createElement('option');
      opt.value = t.slug;
      const short = (t.summary || '').slice(0, 50);
      opt.textContent = short ? `${t.slug}  ·  ${short}` : t.slug;
      els.thread.appendChild(opt);
    }
  }
  populateAskDropdown();
}

async function loadConcepts() {
  try {
    const r = await callBridge({ op: 'list-concepts' });
    if (r && r.ok) cachedConcepts = (r.concepts || []).filter((c) => c.state !== 'archived');
  } catch { cachedConcepts = []; }
}

function populateAskDropdown() {
  els.askThread.innerHTML = '';
  const threads = cachedThreads;
  if (threads.length > 0) {
    const g = document.createElement('optgroup');
    g.label = 'Threads';
    for (const t of threads) {
      const o = document.createElement('option');
      o.value = `thread:${t.slug}`;
      o.textContent = t.slug;
      g.appendChild(o);
    }
    els.askThread.appendChild(g);
  }
  if (cachedConcepts.length > 0) {
    const g = document.createElement('optgroup');
    g.label = 'Concepts';
    for (const c of cachedConcepts) {
      const o = document.createElement('option');
      o.value = `concept:${c.slug}`;
      o.textContent = c.slug;
      g.appendChild(o);
    }
    els.askThread.appendChild(g);
  }
  const d = document.createElement('option');
  d.disabled = true; d.textContent = '──────────';
  els.askThread.appendChild(d);
  const a = document.createElement('option');
  a.value = '__all__'; a.textContent = '— All threads —';
  els.askThread.appendChild(a);
  if (threads.length > 0) els.askThread.value = `thread:${threads[0].slug}`;
}

// ---------- Capture tab logic ----------

async function loadCurrentTab() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab) {
      els.title.textContent = tab.title || '';
      els.url.textContent = formatUrl(tab.url || '');
      els.url.title = tab.url || '';
      els.url.dataset.fullUrl = tab.url || '';
      setFavicon(tab.url);
    }
  } catch {}
}

async function flushDraft() {
  if (!currentDraftUrl) return;
  try {
    const key = `draft:${currentDraftUrl}`;
    if (els.content.value.trim()) {
      await chrome.storage.local.set({ [key]: { content: els.content.value, thread: els.thread.value, savedAt: Date.now() } });
    } else { await chrome.storage.local.remove(key); }
  } catch {}
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
    const r = await callBridge({ op: 'list-threads' });
    if (r && r.ok) {
      populateThreads(r.threads || []);
      setStatus('Connected', 'connected');
      hideConnectionHelp();
    } else {
      setStatus('Bridge error', 'error');
    }
  } catch {
    setStatus('Not connected', 'error');
    showConnectionHelp();
  }
}

function showConnectionHelp() {
  // Make the status clickable — click copies the fix command
  const extId = chrome.runtime.id;
  const command = `bash ~/.vibenote/scripts/vn-link-extension.sh ${extId}`;

  setStatus('Not connected — click to copy fix', 'error clickable');

  els.status.title = command;
  els.status.style.cursor = 'pointer';
  els.status.onclick = () => {
    navigator.clipboard.writeText(command);
    setStatus('Copied ✓ paste in terminal, reload extension', 'success');
    setTimeout(() => {
      setStatus('Not connected — click to copy fix', 'error clickable');
      els.status.style.cursor = 'pointer';
    }, 3000);
  };
}

function hideConnectionHelp() {
  els.status.onclick = null;
  els.status.style.cursor = '';
}

async function loadPing() {
  try {
    const r = await callBridge({ op: 'ping' });
    if (r && r.ok) {
      vaultPath = r.vault || '';
      if (r.claude_config_dir) setConfigIndicator(r.claude_config_dir);
    }
  } catch {}
}

async function restoreDraft() {
  if (!currentDraftUrl) return;
  try {
    const key = `draft:${currentDraftUrl}`;
    const s = await chrome.storage.local.get(key);
    if (s[key]) { els.content.value = s[key].content || ''; if (s[key].thread) els.thread.value = s[key].thread; }
  } catch {}
}
async function saveDraft() {
  if (!currentDraftUrl) return;
  try {
    const key = `draft:${currentDraftUrl}`;
    if (els.content.value.trim()) {
      await chrome.storage.local.set({ [key]: { content: els.content.value, thread: els.thread.value, savedAt: Date.now() } });
    } else { await chrome.storage.local.remove(key); }
  } catch {}
}
async function clearDraft() {
  if (!currentDraftUrl) return;
  try { await chrome.storage.local.remove(`draft:${currentDraftUrl}`); } catch {}
}

async function handleCapture() {
  const content = els.content.value.trim();
  const title = els.title.textContent.trim();
  const url = els.url.dataset.fullUrl || '';
  if (!content && !title && !url) { setStatus('Nothing to capture', 'error'); setTimeout(() => setStatus('Connected', 'connected'), 2000); return; }
  const isBookmark = !content;
  const isAuto = !els.thread.value;
  els.save.disabled = true;
  if (isAuto && !isBookmark) { setStatus('Classifying & capturing…', 'connecting'); els.save.querySelector('.btn-label').textContent = 'Classifying…'; }
  else setStatus(isBookmark ? 'Bookmarking…' : 'Capturing…', 'connecting');
  try {
    const r = await callBridge({ op: 'capture', title, url, content, thread: els.thread.value || undefined }, 60000);
    if (r && r.ok) {
      const tl = (r.threads || [r.thread]).join(', ');
      const hasNew = (r.created_new || []).length > 0;
      const verb = isBookmark ? 'Bookmarked' : 'Captured';
      setStatus(`${verb} to ${tl}${hasNew ? ' (new)' : ''}`, 'success');
      els.save.classList.add('success');
      els.save.querySelector('.btn-label').textContent = verb;
      setTimeout(() => { els.save.classList.remove('success'); els.save.querySelector('.btn-label').textContent = 'Capture'; }, 1800);
      els.content.value = '';
      await clearDraft();
      if (hasNew) loadThreads();
      setTimeout(() => setStatus('Connected', 'connected'), 4000);
    } else setStatus(r?.error || 'Capture failed', 'error');
  } catch (err) { setStatus('Bridge error: ' + err.message, 'error'); }
  finally { els.save.disabled = false; }
}

// ---------- Chat rendering ----------

function renderMarkdown(text) {
  let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  html = html.replace(/\(from ([a-z0-9][a-z0-9-]*)\)/g, '<a class="citation" data-slug="$1" href="#">$1</a>');
  // Lists
  const lines = html.split('\n');
  const out = [];
  let inList = false;
  for (const line of lines) {
    const m = line.match(/^[-*] (.+)$/);
    if (m) { if (!inList) { out.push('<ul>'); inList = true; } out.push(`<li>${m[1]}</li>`); }
    else { if (inList) { out.push('</ul>'); inList = false; } out.push(line); }
  }
  if (inList) out.push('</ul>');
  html = out.join('\n');
  // Paragraphs
  html = html.split(/\n\n+/).map((b) => {
    const t = b.trim();
    if (!t) return '';
    if (t.startsWith('<h') || t.startsWith('<ul') || t.startsWith('<ol')) return t;
    return `<p>${t.replace(/\n/g, ' ')}</p>`;
  }).join('\n');
  return html;
}

function parseNumberedItems(text) {
  const items = [];
  const regex = /^(\d+)\.\s+\*\*(.+?)\*\*\.?\s*([\s\S]*?)(?=^\d+\.\s+\*\*|\n\n(?=[^*\d])|$)/gm;
  let match;
  while ((match = regex.exec(text)) !== null) {
    items.push({ num: match[1], title: match[2], desc: match[3].trim() });
  }
  // Fallback: simpler pattern
  if (items.length === 0) {
    const simpler = /^(\d+)\.\s+\*\*(.+?)\*\*/gm;
    while ((match = simpler.exec(text)) !== null) {
      items.push({ num: match[1], title: match[2], desc: '' });
    }
  }
  return items;
}

function detectHighlight(text) {
  // Look for "highest leverage", "start here", "most important", "highest priority"
  const m = text.match(/highest.leverage.*?#(\d+)|start.with.*?#(\d+)|most.important.*?#(\d+)|highest.priority.*?#(\d+)/i);
  if (m) return m[1] || m[2] || m[3] || m[4];
  return null;
}

function createIconBtn(icon, tooltip, onClick) {
  const btn = document.createElement('button');
  btn.className = 'msg-icon-btn';
  btn.innerHTML = ICONS[icon] || '';
  btn.setAttribute('data-tooltip', tooltip);
  btn.addEventListener('click', onClick);
  return btn;
}

function createItemAction(icon, label, onClick) {
  const btn = document.createElement('button');
  btn.className = 'item-action';
  btn.innerHTML = `${ICONS[icon] || ''} ${label}`;
  btn.addEventListener('click', onClick);
  return btn;
}

function renderMessage(msg, index) {
  const div = document.createElement('div');
  div.className = `msg msg-${msg.role}`;

  if (msg.role === 'user') {
    div.textContent = msg.content;
    return div;
  }

  // Assistant message
  const meta = document.createElement('div');
  meta.className = 'msg-meta';
  meta.textContent = msg.meta || '';
  div.appendChild(meta);

  // Check if this is a chip response with parseable items
  const isChipResponse = !!msg.queryType;
  const items = isChipResponse ? parseNumberedItems(msg.rawContent || msg.content) : [];
  const highlightNum = isChipResponse ? detectHighlight(msg.rawContent || msg.content) : null;

  if (items.length > 0) {
    // Render preamble (text before first numbered item)
    const preambleEnd = (msg.rawContent || msg.content).indexOf(`${items[0].num}. **`);
    if (preambleEnd > 0) {
      const preamble = document.createElement('div');
      preamble.className = 'msg-body';
      preamble.innerHTML = renderMarkdown((msg.rawContent || msg.content).slice(0, preambleEnd).trim());
      div.appendChild(preamble);
    }

    // Render each item as a card
    for (const item of items) {
      const card = document.createElement('div');
      card.className = 'msg-item' + (item.num === highlightNum ? ' msg-item-highlight' : '');

      const title = document.createElement('div');
      title.className = 'msg-item-title';
      title.textContent = `${item.num}. ${item.title}`;
      card.appendChild(title);

      if (item.desc) {
        const desc = document.createElement('div');
        desc.className = 'msg-item-desc';
        desc.innerHTML = renderMarkdown(item.desc);
        card.appendChild(desc);
      }

      // Per-item actions
      const actions = document.createElement('div');
      actions.className = 'msg-item-actions';
      actions.appendChild(createItemAction('task', 'Task', () => {
        sendChat(`Create a task definition for: "${item.title}"\n\nStructure with these sections:\n- **Context:** Background and relevant information from the notes\n- **Objective:** What needs to be accomplished\n- **Goal:** The desired end state\n- **Acceptance criteria:** How to know when it is done\n- **Suggested approach:** Step-by-step plan\n\nWrite in third person. Do not use "you" or "your" — this task may be shared with team members or other tools.`);
      }));
      actions.appendChild(createItemAction('deeper', 'Deeper', () => {
        sendChat(`Explain "${item.title}" in more detail. What are the key considerations, potential approaches, and what would a good first step look like?`);
      }));
      actions.appendChild(createItemAction('copy', 'Copy', () => {
        navigator.clipboard.writeText(`${item.title}\n${item.desc}`);
        actions.querySelector('.item-action:last-child').innerHTML = `${ICONS.copy} Copied`;
        setTimeout(() => actions.querySelector('.item-action:last-child').innerHTML = `${ICONS.copy} Copy`, 1500);
      }));
      card.appendChild(actions);
      div.appendChild(card);
    }

    // Render closing text (after all items — e.g., "highest leverage is #2")
    const lastItem = items[items.length - 1];
    const lastItemEnd = (msg.rawContent || msg.content).lastIndexOf(lastItem.desc || lastItem.title);
    if (lastItemEnd > -1) {
      const afterItems = (msg.rawContent || msg.content).slice(lastItemEnd + (lastItem.desc || lastItem.title).length).trim();
      if (afterItems && afterItems.length > 20) {
        const closing = document.createElement('div');
        closing.className = 'msg-body';
        closing.style.marginTop = '8px';
        closing.innerHTML = renderMarkdown(afterItems);
        div.appendChild(closing);
      }
    }
  } else {
    // Plain message — render as markdown
    const body = document.createElement('div');
    body.className = 'msg-body';
    body.innerHTML = renderMarkdown(msg.content);
    div.appendChild(body);
  }

  // Message-level icon row (on every assistant message)
  const icons = document.createElement('div');
  icons.className = 'msg-icons';
  icons.appendChild(createIconBtn('like', 'Useful', () => {
    // Future: feed into concept strength
  }));
  icons.appendChild(createIconBtn('comment', 'Follow up', () => {
    els.question.focus();
  }));
  icons.appendChild(createIconBtn('retry', 'Retry', () => {
    if (lastUserQuery) sendChat(lastUserQuery);
  }));
  icons.appendChild(createIconBtn('share', 'Share', () => {
    const scope = parseScope(els.askThread.value);
    const ctx = scope.slug ? `From my ${scope.slug} notes` : 'From my Vibenote notes';
    navigator.clipboard.writeText(`${ctx}:\n\n${msg.rawContent || msg.content}`);
  }));
  icons.appendChild(createIconBtn('copy', 'Copy', () => {
    navigator.clipboard.writeText(msg.rawContent || msg.content);
  }));
  div.appendChild(icons);

  return div;
}

function addMessage(msg) {
  chatHistory.push(msg);
  if (els.chatEmpty) { els.chatEmpty.remove(); }
  const el = renderMessage(msg, chatHistory.length - 1);
  els.chatMessages.appendChild(el);
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
  return el;
}

function addLoadingMessage() {
  const div = document.createElement('div');
  div.className = 'msg-loading';
  div.id = 'chat-loading';
  div.innerHTML = `<div class="spinner"></div> Thinking…`;
  els.chatMessages.appendChild(div);
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
  return div;
}

function removeLoadingMessage() {
  const el = document.getElementById('chat-loading');
  if (el) el.remove();
}

// ---------- Chat ask flow ----------

function parseScope(value) {
  if (!value || value === '__all__') return { type: 'all', slug: null };
  if (value.startsWith('thread:')) return { type: 'thread', slug: value.slice(7) };
  if (value.startsWith('concept:')) return { type: 'concept', slug: value.slice(8) };
  return { type: 'thread', slug: value };
}

const CHIP_PROMPTS = {
  'where-am-i': {
    thread: 'Summarize where I currently am with this thread. What are my key decisions, current direction, and what\'s in flight? Keep it concise.',
    all: 'Give me a quick state of my whole vault: which threads are active, what\'s the latest thinking in each?',
  },
  'open-questions': {
    thread: 'What are the open questions in this thread? List each one with context.',
    all: 'What are all my open questions across every thread? Group by thread.',
  },
  'next-steps': {
    thread: 'Based on everything in this thread, what should I work on next? Suggest specific next actions grounded in my notes. Number each action as "1. **Title.** Description".',
    all: 'Based on my recent captures and open questions across all threads, what should I work on next? Number each action as "1. **Title.** Description".',
  },
};

async function sendChat(text, queryType) {
  const question = text.trim();
  if (!question) return;

  lastUserQuery = question;

  // Add user message
  addMessage({ role: 'user', content: question });
  els.question.value = '';

  const scope = parseScope(els.askThread.value);
  const loading = addLoadingMessage();

  // Disable inputs
  els.askSubmit.disabled = true;
  els.chatChips.forEach(c => c.disabled = true);

  try {
    const payload = { op: 'ask', question };
    if (scope.type === 'thread' && scope.slug) {
      payload.thread = scope.slug;
    } else if (scope.type === 'concept' && scope.slug) {
      try {
        const cd = await callBridge({ op: 'read-concept', slug: scope.slug });
        if (cd && cd.ok && cd.body) {
          payload.question = `About the concept "${scope.slug}": ${question}\n\nCONCEPT PAGE:\n${cd.body}`;
        }
      } catch {}
    }

    const r = await callBridge(payload, 90000);
    removeLoadingMessage();

    if (r && r.ok) {
      const latency = (r.latency_ms / 1000).toFixed(1);
      addMessage({
        role: 'assistant',
        content: r.answer,
        rawContent: r.answer,
        meta: `${latency}s · ${r.scope || 'all'}`,
        queryType: queryType || null,
      });
    } else {
      addMessage({ role: 'assistant', content: `Error: ${r?.error || 'Ask failed'}`, meta: 'error' });
    }
  } catch (err) {
    removeLoadingMessage();
    addMessage({ role: 'assistant', content: `Bridge error: ${err.message}`, meta: 'error' });
  } finally {
    els.askSubmit.disabled = false;
    els.chatChips.forEach(c => c.disabled = false);
  }
}

// ---------- Event wiring ----------

els.save.addEventListener('click', handleCapture);
els.askSubmit.addEventListener('click', () => sendChat(els.question.value));

document.addEventListener('keydown', (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    e.preventDefault();
    if (activeTab === 'capture') handleCapture();
    else sendChat(els.question.value);
  }
});

// Auto-resize textarea
els.question.addEventListener('input', () => {
  els.question.style.height = 'auto';
  els.question.style.height = Math.min(els.question.scrollHeight, 120) + 'px';
});

// Chip buttons
els.chatChips.forEach((btn) => {
  btn.addEventListener('click', () => {
    const type = btn.dataset.queryType;
    const prompts = CHIP_PROMPTS[type];
    if (!prompts) return;
    const scope = parseScope(els.askThread.value);
    const prompt = (scope.type === 'thread' || scope.type === 'concept') ? prompts.thread : prompts.all;
    sendChat(prompt, type);
  });
});

// Clear chat on thread change
els.askThread.addEventListener('change', () => {
  chatHistory = [];
  els.chatMessages.innerHTML = '';
  const empty = document.createElement('div');
  empty.className = 'chat-empty';
  empty.id = 'chat-empty';
  empty.innerHTML = `<div class="chat-empty-icon">💭</div><div class="chat-empty-text">Ask anything about your captured thinking.<br>Try a quick query below.</div>`;
  els.chatMessages.appendChild(empty);
});

// Draft autosave
let draftTimer = null;
els.content.addEventListener('input', () => { clearTimeout(draftTimer); draftTimer = setTimeout(saveDraft, 500); });
els.thread.addEventListener('change', saveDraft);

// Contenteditable title
els.title.addEventListener('paste', (e) => { e.preventDefault(); document.execCommand('insertText', false, e.clipboardData.getData('text/plain')); });
els.title.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); els.content.focus(); } });

// Tab change listeners
chrome.tabs.onActivated.addListener(async () => { await refreshForCurrentTab(); });
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (!changeInfo.url || !tab.active) return;
  await refreshForCurrentTab();
});

// ---------- Boot ----------

(async () => {
  setStatus('Connecting…', 'connecting');
  await loadCurrentTab();
  currentDraftUrl = els.url.dataset.fullUrl || '';
  await loadPing();
  await loadConcepts();
  await loadThreads();
  await restoreDraft();
  els.content.focus();
})();
