from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bookdrop</title>
<style>
  :root {
    --bg: #f6f4ef;
    --card-bg: #ffffff;
    --card-hover: #fbfaf7;
    --text: #201d1a;
    --muted: #7a7570;
    --border: #e7e2d9;
    --accent: #3d5a80;
    --accent-soft: #eef2f7;
    --badge-announced: #b5651d;
    --badge-announced-bg: #fbe9d9;
    --badge-released: #2f7a4f;
    --badge-released-bg: #e3f3e8;
    --shadow: 0 1px 2px rgba(20, 16, 8, 0.04), 0 8px 20px -12px rgba(20, 16, 8, 0.12);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #17161a;
      --card-bg: #201f24;
      --card-hover: #26252b;
      --text: #ece9e4;
      --muted: #9a958f;
      --border: #322f36;
      --accent: #8fb0d9;
      --accent-soft: #232a34;
      --badge-announced: #e0a45f;
      --badge-announced-bg: #3a2e1c;
      --badge-released: #6fcb93;
      --badge-released-bg: #1e3226;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 8px 24px -12px rgba(0, 0, 0, 0.5);
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  h1, h2, .book-title, .author-name {
    font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif;
  }
  header {
    position: sticky;
    top: 0;
    z-index: 10;
    background: color-mix(in srgb, var(--bg) 88%, transparent);
    backdrop-filter: blur(10px);
    padding: 1.6rem 1.75rem 1.1rem;
    border-bottom: 1px solid var(--border);
  }
  .header-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem 1.5rem;
    max-width: 68rem;
    margin: 0 auto;
  }
  header h1 { margin: 0; font-size: 1.6rem; letter-spacing: 0.01em; }
  #stats { color: var(--muted); font-size: 0.88rem; }
  #search {
    display: block;
    width: 100%;
    max-width: 68rem;
    margin: 0.9rem auto 0;
    padding: 0.55rem 0.9rem;
    border-radius: 0.6rem;
    border: 1px solid var(--border);
    background: var(--card-bg);
    color: var(--text);
    font-size: 0.95rem;
  }
  #search:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }
  main {
    max-width: 68rem;
    margin: 0 auto;
    padding: 1.5rem 1.75rem 3.5rem;
  }
  #grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(19rem, 1fr));
    gap: 0.9rem;
  }
  details.author {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 0.9rem;
    box-shadow: var(--shadow);
    overflow: hidden;
    align-self: start;
  }
  summary.author-header {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.9rem 1.1rem;
    cursor: pointer;
    user-select: none;
    list-style: none;
  }
  summary.author-header::-webkit-details-marker { display: none; }
  summary.author-header:hover { background: var(--card-hover); }
  .cover-stack {
    display: flex;
    flex-shrink: 0;
    width: 3.4rem;
  }
  .cover-stack img, .cover-stack .cover-fallback {
    width: 2.1rem;
    height: 2.1rem;
    border-radius: 0.3rem;
    object-fit: cover;
    background: var(--accent-soft);
    border: 2px solid var(--card-bg);
    margin-left: -0.9rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
  }
  .cover-stack :first-child { margin-left: 0; }
  .author-meta { flex: 1; min-width: 0; }
  .author-name {
    font-weight: 600;
    font-size: 1.05rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .author-count { color: var(--muted); font-size: 0.82rem; margin-top: 0.1rem; }
  .chevron {
    color: var(--muted);
    transition: transform 0.15s ease;
    flex-shrink: 0;
  }
  details[open] .chevron { transform: rotate(90deg); }
  .books { border-top: 1px solid var(--border); }
  .book {
    display: flex;
    gap: 0.85rem;
    padding: 0.75rem 1.1rem;
    border-bottom: 1px solid var(--border);
  }
  .book:last-child { border-bottom: none; }
  .book img, .book .cover-fallback {
    width: 3rem;
    height: 3rem;
    object-fit: cover;
    border-radius: 0.4rem;
    background: var(--accent-soft);
    flex-shrink: 0;
  }
  .book-info { flex: 1; min-width: 0; }
  .book-title { font-weight: 500; font-size: 0.97rem; line-height: 1.3; }
  .book-series {
    color: var(--accent);
    font-size: 0.78rem;
    margin-top: 0.1rem;
    font-style: italic;
  }
  .book-meta {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 0.3rem;
  }
  .badge {
    display: inline-block;
    padding: 0.12rem 0.55rem;
    border-radius: 1rem;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .badge.announced { color: var(--badge-announced); background: var(--badge-announced-bg); }
  .badge.released { color: var(--badge-released); background: var(--badge-released-bg); }
  #empty, #loading {
    color: var(--muted);
    padding: 4rem 0;
    text-align: center;
    font-size: 0.95rem;
  }
  .spinner {
    width: 1.4rem;
    height: 1.4rem;
    margin: 0 auto 0.75rem;
    border-radius: 50%;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    animation: spin 0.7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<header>
  <div class="header-row">
    <h1>Bookdrop</h1>
    <div id="stats"></div>
  </div>
  <input id="search" type="search" placeholder="Filter authors...">
</header>
<main>
  <div id="loading"><div class="spinner"></div>Loading your shelf...</div>
  <div id="empty" style="display:none">No upcoming or recent books tracked yet.</div>
  <div id="grid"></div>
</main>
<script>
const FORMAT_LABEL = { audiobook: 'Audiobook', book: 'Book' };

async function load() {
  const [authorsRes, booksRes] = await Promise.all([fetch('/authors'), fetch('/books')]);
  const authors = await authorsRes.json();
  const books = await booksRes.json();

  const booksByAuthor = {};
  for (const book of books) {
    (booksByAuthor[book.author_id] ||= []).push(book);
  }
  for (const list of Object.values(booksByAuthor)) {
    list.sort((a, b) => (b.release_date || '').localeCompare(a.release_date || ''));
  }

  const authorsWithBooks = authors
    .filter((author) => (booksByAuthor[author.id] || []).length > 0)
    .sort((a, b) => a.name.localeCompare(b.name));

  document.getElementById('loading').style.display = 'none';
  document.getElementById('stats').textContent =
    books.length + ' book' + (books.length === 1 ? '' : 's') + ' across ' +
    authorsWithBooks.length + ' author' + (authorsWithBooks.length === 1 ? '' : 's');

  if (authorsWithBooks.length === 0) {
    document.getElementById('empty').style.display = 'block';
    return;
  }

  const grid = document.getElementById('grid');

  for (const author of authorsWithBooks) {
    const authorBooks = booksByAuthor[author.id];

    const el = document.createElement('details');
    el.className = 'author';
    el.dataset.name = author.name.toLowerCase();

    const summary = document.createElement('summary');
    summary.className = 'author-header';

    const stack = document.createElement('div');
    stack.className = 'cover-stack';
    for (const book of authorBooks.slice(0, 3)) {
      if (book.cover_url) {
        const img = document.createElement('img');
        img.src = book.cover_url;
        img.loading = 'lazy';
        img.alt = '';
        stack.appendChild(img);
      } else {
        const fallback = document.createElement('div');
        fallback.className = 'cover-fallback';
        stack.appendChild(fallback);
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
    count.textContent = authorBooks.length + ' book' + (authorBooks.length === 1 ? '' : 's');
    meta.appendChild(name);
    meta.appendChild(count);
    summary.appendChild(meta);

    summary.insertAdjacentHTML('beforeend',
      '<svg class="chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="2"><path d="M9 6l6 6-6 6"/></svg>');

    el.appendChild(summary);

    const booksEl = document.createElement('div');
    booksEl.className = 'books';
    for (const book of authorBooks) {
      const row = document.createElement('div');
      row.className = 'book';

      if (book.cover_url) {
        const img = document.createElement('img');
        img.src = book.cover_url;
        img.loading = 'lazy';
        img.alt = '';
        row.appendChild(img);
      } else {
        const fallback = document.createElement('div');
        fallback.className = 'cover-fallback';
        row.appendChild(fallback);
      }

      const info = document.createElement('div');
      info.className = 'book-info';
      const title = document.createElement('div');
      title.className = 'book-title';
      title.textContent = book.title;
      info.appendChild(title);

      if (book.series) {
        const series = document.createElement('div');
        series.className = 'book-series';
        series.textContent = book.series + (book.series_sequence ? ' #' + book.series_sequence : '');
        info.appendChild(series);
      }

      const bmeta = document.createElement('div');
      bmeta.className = 'book-meta';
      const badge = document.createElement('span');
      badge.className = 'badge ' + book.status;
      badge.textContent = book.status;
      bmeta.appendChild(badge);
      bmeta.append((FORMAT_LABEL[book.format] || book.format) + (book.release_date ? ' · ' + book.release_date : ''));
      info.appendChild(bmeta);
      row.appendChild(info);

      booksEl.appendChild(row);
    }
    el.appendChild(booksEl);
    grid.appendChild(el);
  }

  document.getElementById('search').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    for (const el of grid.children) {
      el.style.display = el.dataset.name.includes(q) ? '' : 'none';
    }
  });
}

load().catch((err) => {
  document.getElementById('loading').innerHTML = 'Failed to load: ' + err;
});
</script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML
