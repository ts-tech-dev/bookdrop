from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

router = APIRouter(tags=["ui"])

# The header's brand mark (a drop with an open book cut out of it), with its own light/dark
# colors since a favicon can't inherit the page's CSS variables. The book is a real hole
# (evenodd), so the tab bar shows through it in either theme.
_FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
<style>
  path { fill: #3d5a80; }
  @media (prefers-color-scheme: dark) { path { fill: #93b4dd; } }
</style>
<path fill-rule="evenodd" d="
  M16 1.5C16 1.5 4.5 13.6 4.5 20.5a11.5 11.5 0 0 0 23 0C27.5 13.6 16 1.5 16 1.5Z
  M15 17.2c-2.3-1.5-5-2-7.6-1.8v9.2c2.6-.2 5.3.3 7.6 1.8Z
  M17 17.2c2.3-1.5 5-2 7.6-1.8v9.2c-2.6-.2-5.3.3-7.6 1.8Z"/>
</svg>
"""

_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bookdrop</title>
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
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
  [hidden] { display: none !important; }

  .tabs {
    display: flex;
    gap: 0.25rem;
    margin-top: 0.85rem;
    border-bottom: 1px solid var(--border);
  }
  .tab {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.45rem 0.8rem 0.6rem;
    border: none;
    background: none;
    color: var(--muted);
    font: inherit;
    font-size: 0.92rem;
    font-weight: 600;
    cursor: pointer;
    transition: color 0.15s ease;
  }
  .tab svg { width: 1rem; height: 1rem; }
  .tab:hover { color: var(--text); }
  .tab:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: -2px;
    border-radius: 0.4rem;
  }
  .tab[aria-selected="true"] { color: var(--accent); }
  .tab[aria-selected="true"]::after {
    content: "";
    position: absolute;
    left: 0.55rem;
    right: 0.55rem;
    bottom: -1px;
    height: 2px;
    border-radius: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
  }
  .tab-count {
    min-width: 1.4rem;
    padding: 0.05rem 0.45rem;
    border-radius: 1rem;
    background: var(--accent-soft);
    color: var(--muted);
    font-size: 0.72rem;
    font-variant-numeric: tabular-nums;
    text-align: center;
  }
  .tab-count:empty { display: none; }

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

  .book-action { align-self: center; flex-shrink: 0; }
  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    border: none;
    border-radius: 0.55rem;
    background: none;
    color: var(--muted);
    cursor: pointer;
    transition: opacity 0.15s ease, color 0.15s ease, background 0.15s ease;
  }
  .icon-btn svg { width: 1.05rem; height: 1.05rem; }
  .icon-btn:hover, .icon-btn:focus-visible {
    color: var(--accent-2);
    background: color-mix(in srgb, var(--accent-2) 13%, transparent);
  }
  .icon-btn:focus-visible { outline: 2px solid var(--accent-2); outline-offset: 1px; }
  .icon-btn[disabled] { opacity: 0.4; cursor: default; }
  /* On pointer devices, reveal the remove button on hover/focus so rows stay calm. */
  @media (hover: hover) {
    .book .icon-btn { opacity: 0; }
    .book:hover .icon-btn, .book:focus-within .icon-btn { opacity: 1; }
  }
  .book[data-dismissed="true"] > img, .book[data-dismissed="true"] > .cover-fallback {
    filter: grayscale(0.8);
    opacity: 0.6;
  }
  .book.leaving { animation: leave 0.22s ease forwards; }
  @keyframes leave { to { opacity: 0; transform: translateX(14px); } }
  .chip-count { margin-left: 0.3rem; font-variant-numeric: tabular-nums; opacity: 0.75; }

  #toast {
    position: fixed;
    left: 50%;
    bottom: 1.5rem;
    z-index: 30;
    display: flex;
    align-items: center;
    gap: 0.9rem;
    max-width: calc(100vw - 2rem);
    padding: 0.65rem 0.7rem 0.65rem 1.1rem;
    border-radius: 0.8rem;
    background: var(--text);
    color: var(--bg);
    box-shadow: var(--shadow-lg);
    font-size: 0.88rem;
    opacity: 0;
    pointer-events: none;
    transform: translate(-50%, 0.8rem);
    transition: opacity 0.2s ease, transform 0.2s ease;
  }
  #toast.show { opacity: 1; pointer-events: auto; transform: translate(-50%, 0); }
  #toast.err { background: var(--accent-2); }
  #toast button {
    flex-shrink: 0;
    padding: 0.32rem 0.7rem;
    border: none;
    border-radius: 0.5rem;
    background: color-mix(in srgb, var(--bg) 20%, transparent);
    color: inherit;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
  }
  #toast button:hover { background: color-mix(in srgb, var(--bg) 32%, transparent); }

  .rec-section + .rec-section { margin-top: 2.4rem; }
  .section-title { margin: 0; font-size: 1.3rem; font-weight: 600; letter-spacing: -0.01em; }
  .section-sub { margin: 0.2rem 0 1rem; color: var(--muted); font-size: 0.86rem; }
  .rec-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(19.5rem, 1fr));
    gap: 1rem;
  }
  .rec {
    position: relative;
    display: flex;
    gap: 0.95rem;
    padding: 1rem 1.05rem;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 1rem;
    box-shadow: var(--shadow);
    overflow: hidden;
    animation: rise 0.5s cubic-bezier(0.2, 0.7, 0.3, 1) backwards;
    animation-delay: calc(var(--i, 0) * 35ms);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  }
  .rec::before {
    content: "";
    position: absolute;
    inset: 0 0 auto 0;
    height: 3px;
    background: linear-gradient(90deg, var(--spine, var(--accent)), transparent 78%);
    opacity: 0.85;
  }
  .rec:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
    border-color: color-mix(in srgb, var(--spine, var(--accent)) 45%, var(--border));
  }
  .rec-cover {
    flex-shrink: 0;
    display: block;
    width: 5.4rem;
    height: 5.4rem;
    border-radius: 0.5rem;
    overflow: hidden;
    background: var(--accent-soft);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.18);
  }
  .rec-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .rec-cover .cover-fallback { width: 100%; height: 100%; font-size: 1.8rem; }
  .rec-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
  .rec-title {
    font-family: "Fraunces", Georgia, serif;
    font-weight: 500;
    font-size: 1.04rem;
    line-height: 1.28;
    color: inherit;
    text-decoration: none;
  }
  a.rec-title:hover { color: var(--accent); }
  .rec-author { color: var(--muted); font-size: 0.84rem; margin-top: 0.12rem; }
  .rec-reason {
    display: flex;
    gap: 0.35rem;
    margin-top: 0.45rem;
    color: var(--muted);
    font-size: 0.78rem;
    line-height: 1.35;
  }
  .rec-reason svg {
    width: 0.85rem;
    height: 0.85rem;
    flex-shrink: 0;
    margin-top: 0.1rem;
    color: var(--accent-2);
  }
  .rec-actions {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.4rem;
    margin-top: auto;
    padding-top: 0.65rem;
  }
  .mini-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.28rem 0.65rem;
    border-radius: 0.55rem;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 0.75rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
  }
  .mini-btn svg { width: 0.8rem; height: 0.8rem; }
  .mini-btn:hover:not([disabled]) {
    color: var(--accent);
    border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
  }
  .mini-btn.following {
    color: var(--badge-released);
    background: var(--badge-released-bg);
    border-color: transparent;
    cursor: default;
  }
  .mini-btn[disabled]:not(.following) { opacity: 0.6; cursor: default; }

  #loading, #empty, #noresults, #recs-loading, #recs-empty {
    color: var(--muted);
    padding: 4.5rem 1rem;
    text-align: center;
    font-size: 0.95rem;
  }
  .hint { font-size: 0.85rem; margin-top: 0.35rem; opacity: 0.85; }
  #empty svg, #noresults svg, #recs-empty svg {
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
      <svg class="brand-icon" viewBox="0 0 32 32" fill="currentColor" aria-hidden="true">
        <path fill-rule="evenodd" d="
          M16 1.5C16 1.5 4.5 13.6 4.5 20.5a11.5 11.5 0 0 0 23 0C27.5 13.6 16 1.5 16 1.5Z
          M15 17.2c-2.3-1.5-5-2-7.6-1.8v9.2c2.6-.2 5.3.3 7.6 1.8Z
          M17 17.2c2.3-1.5 5-2 7.6-1.8v9.2c-2.6-.2-5.3.3-7.6 1.8Z"/>
      </svg>
      <h1 class="display">Bookdrop</h1>
    </div>
    <p class="tagline">New books and audiobooks from the authors you follow.</p>
    <div class="tabs" role="tablist" aria-label="Views">
      <button class="tab" id="tab-shelf" role="tab" aria-selected="true"
        aria-controls="panel-shelf" data-tab="shelf">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/>
          <path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3"/>
        </svg>
        New releases
      </button>
      <button class="tab" id="tab-recs" role="tab" aria-selected="false"
        aria-controls="panel-recs" data-tab="for-you" tabindex="-1">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 3l2.4 5.3 5.6.6-4.2 3.8 1.2 5.6L12 15.4l-5 2.9 1.2-5.6L4 8.9l5.6-.6z"/>
        </svg>
        For you
        <span class="tab-count" id="recs-count"></span>
      </button>
    </div>
    <div class="toolbar" id="shelf-toolbar">
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
        <button class="chip" data-filter="hidden" id="hidden-chip" hidden
          title="Books you stopped monitoring">Hidden<span class="chip-count"
          id="c-hidden"></span></button>
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
    <div class="toolbar" id="recs-toolbar" hidden>
      <button id="recs-refresh" class="chip action" type="button"
        title="Rebuild recommendations from your Audiobookshelf library now">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12a9 9 0 1 1-3-6.7M21 4v5h-5"/>
        </svg>
        Refresh recommendations
      </button>
      <span id="recs-status" class="sync-status" role="status" aria-live="polite"></span>
    </div>
    <div id="stats" class="stats" style="display:none">
      <span><strong id="c-books">0</strong> books</span>
      <span class="stat-sep">&middot;</span>
      <span><strong id="c-authors">0</strong> authors</span>
    </div>
  </div>
</header>
<main>
<section id="panel-shelf" role="tabpanel" aria-labelledby="tab-shelf">
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
    <div id="noresults-text">Nothing matches that filter.</div>
  </div>
  <div id="grid"></div>
</section>
<section id="panel-recs" role="tabpanel" aria-labelledby="tab-recs" hidden>
  <div id="recs-loading"><div class="spinner"></div>Finding your next read&hellip;</div>
  <div id="recs-empty" hidden>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"
      stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 3l2.4 5.3 5.6.6-4.2 3.8 1.2 5.6L12 15.4l-5 2.9 1.2-5.6L4 8.9l5.6-.6z"/>
    </svg>
    <div>No recommendations yet.</div>
    <div class="hint">They&rsquo;re built from your Audiobookshelf library &mdash;
      use &ldquo;Refresh recommendations&rdquo; to build them now.</div>
  </div>
  <div id="recs-content" hidden>
    <section class="rec-section" id="sec-series">
      <h2 class="section-title display">Continue a series</h2>
      <p class="section-sub">The next book in series you&rsquo;ve started.</p>
      <div class="rec-grid" id="grid-series"></div>
    </section>
    <section class="rec-section" id="sec-similar">
      <h2 class="section-title display">You might like</h2>
      <p class="section-sub">Titles Audible pairs with books recently added to your
        library.</p>
      <div class="rec-grid" id="grid-similar"></div>
    </section>
  </div>
</section>
</main>
<div id="toast" role="status" aria-live="polite"><span id="toast-text"></span></div>
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
      const dismissed = row.dataset.dismissed === 'true';
      const ok = activeFilter === 'hidden' ? dismissed
        : !dismissed && (activeFilter === 'all' || row.dataset.status === activeFilter);
      row.style.display = ok ? '' : 'none';
      if (ok) visible++;
    }
    const show = nameMatch && visible > 0;
    card.style.display = show ? '' : 'none';
    // Hidden books are what you came to that view for; don't make you expand each author.
    if (show && activeFilter === 'hidden') card.open = true;
    if (show) shown++;
  }
  $('noresults-text').textContent = activeFilter === 'hidden'
    ? 'No hidden books.' : 'Nothing matches that filter.';
  $('noresults').style.display = (shown === 0 && grid.children.length > 0) ? 'block' : 'none';
}

function bookCountText(rows) {
  const active = rows.filter((r) => r.dataset.dismissed !== 'true');
  if (!active.length) return 'All hidden';
  const upcoming = active.filter((r) => r.dataset.status === 'announced').length;
  return active.length + ' book' + (active.length === 1 ? '' : 's') +
    (upcoming ? ' · ' + upcoming + ' upcoming' : '');
}

// Recomputes the header stats, per-author counts and the Hidden chip from the rows, so
// they stay right as books are hidden and restored.
function updateCounts(animate) {
  let books = 0;
  let authors = 0;
  let hidden = 0;
  for (const card of $('grid').children) {
    const rows = [...card.querySelectorAll('.book')];
    card.querySelector('.author-count').textContent = bookCountText(rows);
    const active = rows.filter((r) => r.dataset.dismissed !== 'true').length;
    books += active;
    hidden += rows.length - active;
    if (active) authors++;
  }
  if (animate) {
    countUp($('c-books'), books);
    countUp($('c-authors'), authors);
  } else {
    $('c-books').textContent = books;
    $('c-authors').textContent = authors;
  }
  $('c-hidden').textContent = hidden ? String(hidden) : '';
  $('hidden-chip').hidden = hidden === 0 && activeFilter !== 'hidden';
}

const EYE_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M10.7 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-2.2 3.2"/>' +
  '<path d="M6.6 6.6C3.6 8.6 2 12 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6"/>' +
  '<path d="M9.9 9.9a3 3 0 0 0 4.2 4.2M3 3l18 18"/></svg>';
const RESTORE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5"/></svg>';

let toastTimer = null;

function toast(message, action, isError) {
  const el = $('toast');
  clearTimeout(toastTimer);
  $('toast-text').textContent = message;
  el.querySelector('button')?.remove();
  if (action) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = action.label;
    btn.addEventListener('click', () => {
      el.classList.remove('show');
      action.run();
    });
    el.appendChild(btn);
  }
  el.classList.toggle('err', !!isError);
  el.classList.add('show');
  toastTimer = setTimeout(() => el.classList.remove('show'), action ? 7000 : 4000);
}

function setRowDismissed(row, dismissed) {
  row.dataset.dismissed = String(dismissed);
  const btn = row.querySelector('.book-action');
  const title = row.dataset.title;
  if (dismissed) {
    btn.className = 'book-action mini-btn';
    btn.innerHTML = RESTORE + 'Restore';
    btn.title = 'Start monitoring this book again';
    btn.setAttribute('aria-label', 'Restore ' + title);
  } else {
    btn.className = 'book-action icon-btn';
    btn.innerHTML = EYE_OFF;
    btn.title = 'Not interested — stop monitoring this book';
    btn.setAttribute('aria-label', 'Stop monitoring ' + title);
  }
}

async function setDismissed(row, dismissed) {
  const btn = row.querySelector('.book-action');
  btn.disabled = true;
  try {
    const res = await fetch('/books/' + row.dataset.id + '/dismiss',
      { method: dismissed ? 'POST' : 'DELETE' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
  } catch (err) {
    btn.disabled = false;
    toast('Couldn’t update “' + row.dataset.title + '”: ' + err.message, null, true);
    return;
  }

  const finish = () => {
    row.classList.remove('leaving');
    setRowDismissed(row, dismissed);
    btn.disabled = false;
    updateCounts(false);
    applyFilters();
  };
  // The row leaves whichever view it's in (the shelf when hiding, Hidden when restoring).
  if (RM) finish();
  else {
    row.classList.add('leaving');
    setTimeout(finish, 220);
  }

  if (dismissed) {
    toast('Stopped monitoring “' + row.dataset.title + '”',
      { label: 'Undo', run: () => setDismissed(row, false) });
  } else {
    toast('Monitoring “' + row.dataset.title + '” again');
  }
}

async function load() {
  const [authorsRes, booksRes] = await Promise.all([fetch('/authors'),
    fetch('/books?include_dismissed=true')]);
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
      row.dataset.id = String(b.id);
      row.dataset.title = b.title;

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

      const action = document.createElement('button');
      action.type = 'button';
      action.className = 'book-action';
      action.addEventListener('click', () => {
        setDismissed(row, row.dataset.dismissed !== 'true');
      });
      row.appendChild(action);
      setRowDismissed(row, b.dismissed);

      booksEl.appendChild(row);
    }
    el.appendChild(booksEl);
    grid.appendChild(el);
  }

  updateCounts(true);
  applyFilters();

  $('search').addEventListener('input', applyFilters);
  for (const chip of document.querySelectorAll('.chips .chip')) {
    chip.addEventListener('click', () => {
      const cur = document.querySelector('.chips .chip.is-active');
      if (cur) cur.classList.remove('is-active');
      chip.classList.add('is-active');
      activeFilter = chip.dataset.filter;
      updateCounts(false);
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

function showTab(name) {
  const recs = name === 'for-you';
  for (const tab of document.querySelectorAll('.tab')) {
    const on = tab.dataset.tab === (recs ? 'for-you' : 'shelf');
    tab.setAttribute('aria-selected', String(on));
    tab.tabIndex = on ? 0 : -1;
  }
  $('panel-shelf').hidden = recs;
  $('shelf-toolbar').hidden = recs;
  $('stats').hidden = recs;
  $('panel-recs').hidden = !recs;
  $('recs-toolbar').hidden = !recs;
  const hash = recs ? '#for-you' : '';
  if (location.hash !== hash) {
    history.replaceState(null, '', location.pathname + location.search + hash);
  }
}

for (const tab of document.querySelectorAll('.tab')) {
  tab.addEventListener('click', () => showTab(tab.dataset.tab));
  tab.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    const tabs = [...document.querySelectorAll('.tab')];
    const next = tabs[(tabs.indexOf(tab) + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) %
      tabs.length];
    showTab(next.dataset.tab);
    next.focus();
  });
}
window.addEventListener('hashchange', () => showTab(location.hash.slice(1)));

const SPARK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
  'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5' +
  'M15.5 8.5L18 6"/></svg>';
const PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" ' +
  'stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
const CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" ' +
  'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';

let followed = new Set();

function ago(iso) {
  // DB timestamps are naive UTC.
  const t = new Date(/Z|[+-]\\d\\d:\\d\\d$/.test(iso) ? iso : iso + 'Z');
  const m = Math.round((Date.now() - t) / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return m + ' min ago';
  const h = Math.round(m / 60);
  if (h < 24) return h + ' h ago';
  const d = Math.round(h / 24);
  return d + ' day' + (d === 1 ? '' : 's') + ' ago';
}

function setFollowing(btn) {
  btn.classList.add('following');
  btn.disabled = true;
  btn.innerHTML = CHECK + 'Following';
}

async function follow(name, btn) {
  btn.disabled = true;
  const status = $('recs-status');
  status.classList.remove('err');
  try {
    const res = await fetch('/authors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    followed.add(name.toLowerCase());
    for (const other of document.querySelectorAll('.follow-btn')) {
      if (other.dataset.author === name.toLowerCase()) setFollowing(other);
    }
    status.textContent = 'Following ' + name +
      ' — their releases appear under New releases after the next check.';
  } catch (err) {
    btn.disabled = false;
    status.classList.add('err');
    status.textContent = 'Could not follow ' + name + ': ' + err.message;
  }
}

// Goodreads has no ID we can derive from an Audible ASIN, so link to a title + author
// search. Its iOS/Android apps claim goodreads.com links, so phones open the app.
function goodreadsUrl(r) {
  const q = [r.title, r.author_name].filter(Boolean).join(' ');
  return 'https://www.goodreads.com/search?q=' + encodeURIComponent(q);
}

function recCard(r, i) {
  const card = document.createElement('article');
  card.className = 'rec';
  card.style.setProperty('--i', String(Math.min(i, 12)));
  card.style.setProperty('--spine', 'hsl(' + hueFor(r.author_name || r.title) + ' 58% 55%)');

  const link = goodreadsUrl(r);
  const cover = document.createElement('a');
  cover.className = 'rec-cover';
  cover.href = link;
  cover.target = '_blank';
  cover.rel = 'noopener';
  cover.tabIndex = -1;
  cover.setAttribute('aria-hidden', 'true');
  if (r.cover_url) {
    const img = document.createElement('img');
    img.src = r.cover_url;
    img.loading = 'lazy';
    img.alt = '';
    cover.appendChild(img);
  } else {
    const fb = document.createElement('div');
    fb.className = 'cover-fallback';
    fb.textContent = initial(r.title);
    cover.appendChild(fb);
  }
  card.appendChild(cover);

  const info = document.createElement('div');
  info.className = 'rec-info';

  const title = document.createElement('a');
  title.className = 'rec-title';
  title.textContent = r.title;
  title.href = link;
  title.target = '_blank';
  title.rel = 'noopener';
  title.title = 'Open on Goodreads';
  info.appendChild(title);

  if (r.author_name) {
    const a = document.createElement('div');
    a.className = 'rec-author';
    a.textContent = r.author_name;
    info.appendChild(a);
  }
  if (r.series) {
    const s = document.createElement('div');
    s.className = 'book-series';
    s.textContent = r.series + (r.series_sequence ? ' #' + r.series_sequence : '');
    info.appendChild(s);
  }

  const reason = document.createElement('div');
  reason.className = 'rec-reason';
  reason.insertAdjacentHTML('beforeend', SPARK);
  reason.insertAdjacentText('beforeend', r.reason);
  info.appendChild(reason);

  const actions = document.createElement('div');
  actions.className = 'rec-actions';
  const rel = relRelease(r.release_date);
  if (rel) {
    const c = document.createElement('span');
    c.className = 'countdown' + (rel.soon ? ' soon' : '');
    c.textContent = rel.text;
    actions.appendChild(c);
  }
  if (r.author_name) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'mini-btn follow-btn';
    btn.dataset.author = r.author_name.toLowerCase();
    if (followed.has(btn.dataset.author)) {
      setFollowing(btn);
    } else {
      btn.innerHTML = PLUS + 'Follow author';
      btn.title = 'Track new releases from ' + r.author_name;
      btn.addEventListener('click', () => follow(r.author_name, btn));
    }
    actions.appendChild(btn);
  }
  info.appendChild(actions);

  card.appendChild(info);
  return card;
}

function renderRecs(recs) {
  $('recs-loading').hidden = true;
  $('recs-count').textContent = recs.length ? String(recs.length) : '';
  $('recs-empty').hidden = recs.length > 0;
  $('recs-content').hidden = recs.length === 0;

  const groups = [
    ['next_in_series', 'sec-series', 'grid-series'],
    ['similar', 'sec-similar', 'grid-similar'],
  ];
  for (const [kind, section, gridId] of groups) {
    const list = recs.filter((r) => r.kind === kind);
    const grid = $(gridId);
    grid.replaceChildren(...list.map(recCard));
    $(section).hidden = list.length === 0;
  }

  const status = $('recs-status');
  status.classList.remove('err');
  status.textContent = recs.length ? 'Updated ' + ago(recs[0].created_at) : '';
}

async function loadRecs() {
  const [recsRes, authorsRes] = await Promise.all([
    fetch('/recommendations'), fetch('/authors'),
  ]);
  const recs = await recsRes.json();
  const authors = await authorsRes.json();
  followed = new Set(authors.map((a) => a.name.toLowerCase()));
  renderRecs(recs);
}

$('recs-refresh').addEventListener('click', async () => {
  const btn = $('recs-refresh');
  const status = $('recs-status');
  btn.disabled = true;
  btn.classList.add('spinning');
  status.classList.remove('err');
  status.textContent = 'Reading your library and asking Audible… this can take a minute.';
  try {
    const res = await fetch('/recommendations/refresh', { method: 'POST' });
    const body = await res.json();
    if (!res.ok) throw new Error(body.detail || ('HTTP ' + res.status));
    renderRecs(body);
  } catch (err) {
    status.classList.add('err');
    status.textContent = 'Refresh failed: ' + err.message;
  } finally {
    btn.disabled = false;
    btn.classList.remove('spinning');
  }
});

showTab(location.hash.slice(1));

load().catch((err) => {
  $('loading').innerHTML = 'Failed to load: ' + err;
});
loadRecs().catch((err) => {
  $('recs-loading').innerHTML = 'Failed to load: ' + err;
});
</script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


@router.get("/favicon.svg", include_in_schema=False)
def favicon() -> Response:
    return Response(
        _FAVICON_SVG,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )
