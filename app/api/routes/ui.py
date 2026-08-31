from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bookdrop</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link
  href="https://fonts.googleapis.com/css2?family=Fraunces:wght@400;500;600&display=swap"
  rel="stylesheet">
<style>
  :root {
    --bg: #f4f1ea;
    --card-bg: #ffffff;
    --card-hover: #fbfaf6;
    --text: #201d1a;
    --muted: #79736c;
    --border: #e6e0d5;
    --accent: #3d5a80;
    --accent-2: #c1663b;
    --accent-soft: #eef2f7;
    --badge-announced: #a85c1c;
    --badge-announced-bg: #f9e7d4;
    --badge-released: #2c7449;
    --badge-released-bg: #dff1e6;
    --shadow: 0 1px 2px rgba(20, 16, 8, 0.04), 0 10px 24px -14px rgba(20, 16, 8, 0.16);
    --shadow-lg: 0 2px 6px rgba(20, 16, 8, 0.07), 0 22px 44px -20px rgba(20, 16, 8, 0.28);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #16151a;
      --card-bg: #201f25;
      --card-hover: #27262d;
      --text: #ece9e4;
      --muted: #9a948d;
      --border: #322f38;
      --accent: #93b4dd;
      --accent-2: #e59b64;
      --accent-soft: #232b36;
      --badge-announced: #e3a866;
      --badge-announced-bg: #3b2f1d;
      --badge-released: #74cf98;
      --badge-released-bg: #1d3327;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 10px 26px -14px rgba(0, 0, 0, 0.55);
      --shadow-lg: 0 2px 6px rgba(0, 0, 0, 0.4), 0 24px 48px -20px rgba(0, 0, 0, 0.7);
    }
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    min-height: 100vh;
    background:
      radial-gradient(42rem 42rem at 6% -12%,
        color-mix(in srgb, var(--accent) 14%, transparent), transparent 62%),
      radial-gradient(38rem 38rem at 104% -6%,
        color-mix(in srgb, var(--accent-2) 12%, transparent), transparent 58%),
      var(--bg);
    background-attachment: fixed;
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .display { font-family: "Fraunces", Georgia, "Iowan Old Style", "Palatino Linotype", serif; }

  header {
    position: sticky;
    top: 0;
    z-index: 10;
    background: color-mix(in srgb, var(--bg) 82%, transparent);
    backdrop-filter: blur(12px) saturate(1.1);
    -webkit-backdrop-filter: blur(12px) saturate(1.1);
    border-bottom: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
    padding: 1.5rem 1.75rem 1rem;
    transition: padding 0.2s ease;
  }
  header.scrolled { padding-top: 0.85rem; padding-bottom: 0.7rem; }
  .wrap { max-width: 70rem; margin: 0 auto; }
  .brand { display: flex; align-items: center; gap: 0.7rem; }
  .brand-icon {
    flex-shrink: 0;
    width: 2.1rem;
    height: 2.1rem;
    color: var(--accent);
    animation: float 4s ease-in-out infinite;
    transition: width 0.2s ease, height 0.2s ease;
  }
  @keyframes float { 50% { transform: translateY(-3px); } }
  .brand h1 {
    margin: 0;
    font-size: 1.7rem;
    font-weight: 600;
    letter-spacing: -0.01em;
    background: linear-gradient(115deg, var(--accent), var(--accent-2));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    transition: font-size 0.2s ease;
  }
  header.scrolled .brand h1 { font-size: 1.4rem; }
  header.scrolled .brand-icon { width: 1.7rem; height: 1.7rem; }
  .tagline {
    margin: 0.35rem 0 0;
    color: var(--muted);
    font-size: 0.9rem;
    transition: opacity 0.2s ease;
  }
  header.scrolled .tagline { opacity: 0; height: 0; margin: 0; overflow: hidden; }
  .toolbar {
    display: flex;
    gap: 0.7rem;
    align-items: center;
    flex-wrap: wrap;
    margin-top: 0.9rem;
  }
  .search-box { position: relative; flex: 1; min-width: 12rem; }
  .search-box svg {
    position: absolute;
    left: 0.8rem;
    top: 50%;
    transform: translateY(-50%);
    width: 1rem;
    height: 1rem;
    color: var(--muted);
    pointer-events: none;
  }
  #search {
    width: 100%;
    padding: 0.58rem 0.9rem 0.58rem 2.3rem;
    border-radius: 0.7rem;
    border: 1px solid var(--border);
    background: var(--card-bg);
    color: var(--text);
    font-size: 0.95rem;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }
  #search:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 22%, transparent);
  }
  .chips { display: flex; gap: 0.4rem; }
  .chip {
    padding: 0.5rem 0.9rem;
    border-radius: 0.7rem;
    border: 1px solid var(--border);
    background: var(--card-bg);
    color: var(--muted);
    font: inherit;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
  }
  .chip:hover {
    color: var(--text);
    border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
  }
  .chip.is-active { color: #fff; background: var(--accent); border-color: var(--accent); }
  @media (prefers-color-scheme: dark) { .chip.is-active { color: #16151a; } }
  .chip.action { display: inline-flex; align-items: center; gap: 0.4rem; }
  .chip.action svg { width: 0.9rem; height: 0.9rem; }
  .chip.action[disabled] { opacity: 0.6; cursor: default; }
  .chip.action.spinning svg { animation: spin 0.7s linear infinite; }
  .sync-status { color: var(--muted); font-size: 0.85rem; align-self: center; }
  .sync-status.err { color: var(--accent-2); }
  .stats {
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.85rem;
    color: var(--muted);
    font-size: 0.88rem;
  }
  .stats strong { color: var(--text); font-variant-numeric: tabular-nums; }
  .stat-sep { opacity: 0.5; }

  main { max-width: 70rem; margin: 0 auto; padding: 1.6rem 1.75rem 3rem; }
  #grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(19.5rem, 1fr));
    gap: 1rem;
  }
  details.author {
    position: relative;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 1rem;
    box-shadow: var(--shadow);
    overflow: hidden;
    align-self: start;
    animation: rise 0.5s cubic-bezier(0.2, 0.7, 0.3, 1) backwards;
    animation-delay: calc(var(--i, 0) * 35ms);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  }
  @keyframes rise { from { opacity: 0; transform: translateY(14px); } }
  details.author::before {
    content: "";
    position: absolute;
    inset: 0 0 auto 0;
    height: 3px;
    background: linear-gradient(90deg, var(--spine, var(--accent)), transparent 78%);
    opacity: 0.85;
  }
  details.author:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
    border-color: color-mix(in srgb, var(--spine, var(--accent)) 45%, var(--border));
  }
  details[open].author {
    border-color: color-mix(in srgb, var(--spine, var(--accent)) 35%, var(--border));
  }
  summary.author-header {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.95rem 1.1rem;
    cursor: pointer;
    user-select: none;
    list-style: none;
  }
  summary.author-header::-webkit-details-marker { display: none; }
  summary.author-header:hover { background: var(--card-hover); }
  details[open] summary.author-header {
    background: color-mix(in srgb, var(--accent-soft) 55%, transparent);
  }
  .cover-stack { display: flex; flex-shrink: 0; padding-left: 0.9rem; }
  .cover-stack img, .cover-stack .cover-fallback {
    width: 2.2rem;
    height: 2.2rem;
    border-radius: 0.35rem;
    object-fit: cover;
    background: var(--accent-soft);
    border: 2px solid var(--card-bg);
    margin-left: -0.9rem;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.18);
    transition: transform 0.2s ease;
  }
  .cover-stack :nth-child(1) { transform: rotate(-5deg); }
  .cover-stack :nth-child(3) { transform: rotate(5deg); }
  summary.author-header:hover .cover-stack :nth-child(1) {
    transform: translateX(-2px) rotate(-9deg);
  }
  summary.author-header:hover .cover-stack :nth-child(3) {
    transform: translateX(2px) rotate(9deg);
  }
  .cover-fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: "Fraunces", Georgia, serif;
    font-weight: 600;
    color: var(--accent);
    text-transform: uppercase;
  }
  .author-meta { flex: 1; min-width: 0; }
  .author-name {
    font-family: "Fraunces", Georgia, serif;
    font-weight: 600;
    font-size: 1.08rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .author-count { color: var(--muted); font-size: 0.82rem; margin-top: 0.12rem; }
  .chevron { color: var(--muted); transition: transform 0.18s ease; flex-shrink: 0; }
  details[open] .chevron { transform: rotate(90deg); }

  .books { border-top: 1px solid var(--border); }
  .book {
    display: flex;
    gap: 0.85rem;
    padding: 0.8rem 1.1rem;
    border-bottom: 1px solid var(--border);
  }
  .book:last-child { border-bottom: none; }
  .book > img, .book > .cover-fallback {
    width: 3.1rem;
    height: 3.1rem;
    object-fit: cover;
    border-radius: 0.45rem;
    background: var(--accent-soft);
    flex-shrink: 0;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.14);
    font-size: 1.15rem;
  }
  .book-info { flex: 1; min-width: 0; }
  .book-title {
    font-family: "Fraunces", Georgia, serif;
    font-weight: 500;
    font-size: 1rem;
    line-height: 1.3;
  }
  .book-series {
    color: var(--accent);
    font-size: 0.78rem;
    margin-top: 0.12rem;
    font-style: italic;
  }
  .book-pills {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.35rem;
    margin-top: 0.4rem;
  }
  .book-sub {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 0.3rem;
  }
  .book-sub svg { width: 0.95rem; height: 0.95rem; flex-shrink: 0; }
  .badge, .countdown, .fresh {
    display: inline-flex;
    align-items: center;
    padding: 0.14rem 0.5rem;
    border-radius: 1rem;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .badge::before {
    content: "";
    width: 0.38rem;
    height: 0.38rem;
    border-radius: 50%;
    background: currentColor;
    margin-right: 0.35rem;
  }
  .badge.announced { color: var(--badge-announced); background: var(--badge-announced-bg); }
  .badge.released { color: var(--badge-released); background: var(--badge-released-bg); }
  .countdown {
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 13%, transparent);
    font-variant-numeric: tabular-nums;
  }
  .countdown.soon { color: var(--badge-announced); background: var(--badge-announced-bg); }
  .fresh { color: var(--badge-released); background: var(--badge-released-bg); }
  .fresh::before { content: "✦"; margin-right: 0.3rem; }

  #loading, #empty, #noresults {
    color: var(--muted);
    padding: 4.5rem 1rem;
    text-align: center;
    font-size: 0.95rem;
  }
  #empty svg, #noresults svg {
    width: 2.4rem;
    height: 2.4rem;
    opacity: 0.4;
    margin-bottom: 0.8rem;
  }
  .spinner {
    width: 1.5rem;
    height: 1.5rem;
    margin: 0 auto 0.8rem;
    border-radius: 50%;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  footer {
    max-width: 70rem;
    margin: 0 auto;
    padding: 0 1.75rem 3rem;
    color: var(--muted);
    font-size: 0.8rem;
    text-align: center;
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before { animation: none !important; transition: none !important; }
    html { scroll-behavior: auto; }
  }
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="brand">
      <svg class="brand-icon" viewBox="0 0 32 32" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M3 14a13 13 0 0 1 26 0"/>
        <path d="M3 14c2.3 0 3.6-2.2 4.4-5M29 14c-2.3 0-3.6-2.2-4.4-5M16 3v6M11 14l5 5 5-5"/>
        <rect x="11.5" y="18.5" width="9" height="9.5" rx="1.5"/>
        <path d="M16 19v9.5"/>
      </svg>
      <h1 class="display">Bookdrop</h1>
    </div>
    <p class="tagline">New books and audiobooks from the authors you follow.</p>
    <div class="toolbar">
      <div class="search-box">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round">
          <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>
        </svg>
        <input id="search" type="search" placeholder="Filter authors&hellip;" autocomplete="off">
      </div>
      <div class="chips">
        <button class="chip is-active" data-filter="all">All</button>
        <button class="chip" data-filter="announced">Announced</button>
        <button class="chip" data-filter="released">Released</button>
      </div>
      <button id="sync-btn" class="chip action" type="button"
        title="Re-import the author list from Audiobookshelf now">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12a9 9 0 1 1-3-6.7M21 4v5h-5"/>
        </svg>
        Import authors
      </button>
      <span id="sync-status" class="sync-status" role="status" aria-live="polite"></span>
    </div>
    <div id="stats" class="stats" style="display:none">
      <span><strong id="c-books">0</strong> books</span>
      <span class="stat-sep">&middot;</span>
      <span><strong id="c-authors">0</strong> authors</span>
    </div>
  </div>
</header>
<main>
  <div id="loading"><div class="spinner"></div>Gathering your shelf&hellip;</div>
  <div id="empty" style="display:none">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
      stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/>
      <path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3"/>
    </svg>
    <div>No upcoming or recent books tracked yet.</div>
  </div>
  <div id="noresults" style="display:none">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="2" stroke-linecap="round">
      <circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>
    </svg>
    <div>Nothing matches that filter.</div>
  </div>
  <div id="grid"></div>
</main>
<footer class="wrap">Bookdrop &mdash; your personal new-release radar.</footer>
<script>
const RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (id) => document.getElementById(id);
const FORMAT_LABEL = { audiobook: 'Audiobook', book: 'Book' };
const ICONS = {
  audiobook: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M4 14v-2a8 8 0 0 1 16 0v2"/>' +
    '<rect x="2" y="14" width="5" height="7" rx="1.5"/>' +
    '<rect x="17" y="14" width="5" height="7" rx="1.5"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/>' +
    '<path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3"/></svg>',
};

function initial(str) { return ((str || '').trim()[0] || '?'); }

function hueFor(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) % 360;
  return h;
}

function fmtDate(str) {
  if (!str) return null;
  const d = new Date(str + 'T00:00:00');
  if (isNaN(d.getTime())) return str;
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function relRelease(str) {
  if (!str) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(str + 'T00:00:00');
  const n = Math.round((d - today) / 86400000);
  if (n < 0) return null;
  if (n === 0) return { text: 'Lands today', soon: true };
  if (n === 1) return { text: 'Lands tomorrow', soon: true };
  if (n <= 14) return { text: 'in ' + n + ' days', soon: n <= 7 };
  if (n <= 70) return { text: 'in ' + Math.round(n / 7) + ' weeks', soon: false };
  return { text: 'in ' + Math.round(n / 30) + ' months', soon: false };
}

function justLanded(book) {
  if (book.status !== 'released' || !book.release_date) return false;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(book.release_date + 'T00:00:00');
  const n = Math.round((today - d) / 86400000);
  return n >= 0 && n <= 21;
}

function countUp(el, target) {
  if (RM) { el.textContent = target; return; }
  const dur = 550;
  const start = performance.now();
  (function tick(now) {
    const p = Math.min(1, (now - start) / dur);
    el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * target);
    if (p < 1) requestAnimationFrame(tick);
  })(performance.now());
}

let activeFilter = 'all';

function applyFilters() {
  const grid = $('grid');
  const q = $('search').value.trim().toLowerCase();
  let shown = 0;
  for (const card of grid.children) {
    const nameMatch = card.dataset.name.includes(q);
    let visible = 0;
    for (const row of card.querySelectorAll('.book')) {
      const ok = activeFilter === 'all' || row.dataset.status === activeFilter;
      row.style.display = ok ? '' : 'none';
      if (ok) visible++;
    }
    const show = nameMatch && visible > 0;
    card.style.display = show ? '' : 'none';
    if (show) shown++;
  }
  $('noresults').style.display = (shown === 0 && grid.children.length > 0) ? 'block' : 'none';
}

async function load() {
  const [authorsRes, booksRes] = await Promise.all([fetch('/authors'), fetch('/books')]);
  const authors = await authorsRes.json();
  const books = await booksRes.json();

  const byAuthor = {};
  for (const b of books) (byAuthor[b.author_id] ||= []).push(b);
  for (const list of Object.values(byAuthor)) {
    list.sort((a, b) => (b.release_date || '').localeCompare(a.release_date || ''));
  }

  const withBooks = authors
    .filter((a) => (byAuthor[a.id] || []).length > 0)
    .sort((a, b) => a.name.localeCompare(b.name));

  $('loading').style.display = 'none';

  if (withBooks.length === 0) {
    $('empty').style.display = 'block';
    return;
  }

  $('stats').style.display = 'flex';
  countUp($('c-books'), books.length);
  countUp($('c-authors'), withBooks.length);

  const grid = $('grid');
  let idx = 0;

  for (const author of withBooks) {
    const list = byAuthor[author.id];

    const el = document.createElement('details');
    el.className = 'author';
    el.dataset.name = author.name.toLowerCase();
    el.style.setProperty('--i', String(idx++));
    el.style.setProperty('--spine', 'hsl(' + hueFor(author.name) + ' 58% 55%)');

    const summary = document.createElement('summary');
    summary.className = 'author-header';

    const stack = document.createElement('div');
    stack.className = 'cover-stack';
    for (const b of list.slice(0, 3)) {
      if (b.cover_url) {
        const img = document.createElement('img');
        img.src = b.cover_url;
        img.loading = 'lazy';
        img.alt = '';
        stack.appendChild(img);
      } else {
        const fb = document.createElement('div');
        fb.className = 'cover-fallback';
        fb.textContent = initial(b.title);
        stack.appendChild(fb);
      }
    }
    summary.appendChild(stack);

    const meta = document.createElement('div');
    meta.className = 'author-meta';
    const name = document.createElement('div');
    name.className = 'author-name';
    name.textContent = author.name;
    const count = document.createElement('div');
    count.className = 'author-count';
    const upcoming = list.filter((b) => b.status === 'announced').length;
    count.textContent = list.length + ' book' + (list.length === 1 ? '' : 's') +
      (upcoming ? ' · ' + upcoming + ' upcoming' : '');
    meta.appendChild(name);
    meta.appendChild(count);
    summary.appendChild(meta);

    summary.insertAdjacentHTML('beforeend',
      '<svg class="chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M9 6l6 6-6 6"/></svg>');

    el.appendChild(summary);

    const booksEl = document.createElement('div');
    booksEl.className = 'books';
    for (const b of list) {
      const row = document.createElement('div');
      row.className = 'book';
      row.dataset.status = b.status;

      if (b.cover_url) {
        const img = document.createElement('img');
        img.src = b.cover_url;
        img.loading = 'lazy';
        img.alt = '';
        row.appendChild(img);
      } else {
        const fb = document.createElement('div');
        fb.className = 'cover-fallback';
        fb.textContent = initial(b.title);
        row.appendChild(fb);
      }

      const info = document.createElement('div');
      info.className = 'book-info';

      const title = document.createElement('div');
      title.className = 'book-title';
      title.textContent = b.title;
      info.appendChild(title);

      if (b.series) {
        const s = document.createElement('div');
        s.className = 'book-series';
        s.textContent = b.series + (b.series_sequence ? ' #' + b.series_sequence : '');
        info.appendChild(s);
      }

      const pills = document.createElement('div');
      pills.className = 'book-pills';
      const badge = document.createElement('span');
      badge.className = 'badge ' + b.status;
      badge.textContent = b.status;
      pills.appendChild(badge);

      const rel = b.status === 'announced' ? relRelease(b.release_date) : null;
      if (rel) {
        const c = document.createElement('span');
        c.className = 'countdown' + (rel.soon ? ' soon' : '');
        c.textContent = rel.text;
        pills.appendChild(c);
      }
      if (justLanded(b)) {
        const f = document.createElement('span');
        f.className = 'fresh';
        f.textContent = 'Just landed';
        pills.appendChild(f);
      }
      info.appendChild(pills);

      const sub = document.createElement('div');
      sub.className = 'book-sub';
      sub.insertAdjacentHTML('beforeend', ICONS[b.format] || ICONS.book);
      const dateStr = fmtDate(b.release_date);
      sub.insertAdjacentText('beforeend',
        (FORMAT_LABEL[b.format] || b.format) + (dateStr ? ' · ' + dateStr : ' · Date TBA'));
      info.appendChild(sub);

      row.appendChild(info);
      booksEl.appendChild(row);
    }
    el.appendChild(booksEl);
    grid.appendChild(el);
  }

  $('search').addEventListener('input', applyFilters);
  for (const chip of document.querySelectorAll('.chip')) {
    chip.addEventListener('click', () => {
      const cur = document.querySelector('.chip.is-active');
      if (cur) cur.classList.remove('is-active');
      chip.classList.add('is-active');
      activeFilter = chip.dataset.filter;
      applyFilters();
    });
  }
}

window.addEventListener('scroll', () => {
  document.querySelector('header').classList.toggle('scrolled', window.scrollY > 8);
}, { passive: true });

$('sync-btn').addEventListener('click', async () => {
  const btn = $('sync-btn');
  const status = $('sync-status');
  btn.disabled = true;
  btn.classList.add('spinning');
  status.classList.remove('err');
  status.textContent = 'Importing from Audiobookshelf…';
  try {
    const res = await fetch('/audiobookshelf/import-authors', { method: 'POST' });
    const body = await res.json();
    if (!res.ok) throw new Error(body.detail || ('HTTP ' + res.status));
    const n = Array.isArray(body) ? body.length : 0;
    if (n > 0) {
      status.textContent = 'Added ' + n + ' author' + (n === 1 ? '' : 's') + '. Reloading…';
      setTimeout(() => location.reload(), 900);
    } else {
      status.textContent = 'No new authors.';
    }
  } catch (err) {
    status.classList.add('err');
    status.textContent = 'Import failed: ' + err.message;
  } finally {
    btn.disabled = false;
    btn.classList.remove('spinning');
  }
});

load().catch((err) => {
  $('loading').innerHTML = 'Failed to load: ' + err;
});
</script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML
