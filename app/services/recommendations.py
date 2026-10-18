"""Reading recommendations built from what's in the Audiobookshelf library.

Two kinds, both looked up on Audible by ASIN (Audiobookshelf items without an ASIN can
still rule a title out as "already owned", but can't seed a lookup):

* **Next in series** — for each series in the library, the lowest-numbered book past the
  highest one owned. Series are matched on Audible's own series ID (resolved from an owned
  book), not by name, since Audiobookshelf often splits/renames them ("Fourth Wing #1" and
  "The Empyrean #2" are the same Audible series).
* **Similar** — Audible's "listeners also enjoyed" titles for the most recently added
  books, ranked by how many of those books suggested each title and how highly.

The result is shared by all users and replaces the ``recommendations`` table wholesale.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models import Recommendation
from app.models.enums import RecommendationKind
from app.services.audible import AudibleClient
from app.services.audiobookshelf import AudiobookshelfClient
from app.services.release_tracker import is_english
from app.utils.dates import parse_date

logger = logging.getLogger(__name__)

# Bounds on how much of the library a refresh looks at. Each similar-seed costs one Audible
# request and each series two, so these keep a refresh to roughly a hundred requests.
_SIMILAR_SEEDS = 25
_SIMILAR_PER_SEED = 20
_MAX_SIMILAR = 60
# Similar-title lists are dominated by the seed's own author; cap it so the list isn't just
# the rest of a series the library already has.
_MAX_SIMILAR_PER_AUTHOR = 2
_MAX_SERIES = 40
_AUDIBLE_CONCURRENCY = 4

_BOOK_DELIVERY_TYPES = {"SinglePartBook", "MultiPartBook"}
# Audible lists full-cast adaptations (often split into "Part 1 of 2" products) alongside
# the regular audiobook; recommending those as well is just noise.
_ADAPTATION_RE = re.compile(r"dramati[sz]ed adaptation", re.IGNORECASE)
_COLLECTION_RE = re.compile(
    r"\bbox(ed)? set\b|\bbooks? \d+\s*[-–]\s*\d+\b|\bcomplete series\b|\bomnibus\b",
    re.IGNORECASE,
)
_BRACKETED_RE = re.compile(r"[\(\[].*?[\)\]]")
# Trailing " - GraphicAudio" style edition labels that Audiobookshelf titles often carry.
_DASH_SUFFIX_RE = re.compile(r"\s+-\s+.*$")
# Audible's stand-in release date for "to be announced".
_PLACEHOLDER_YEAR = 2100


class AudibleUnavailableError(Exception):
    """Every Audible lookup in a refresh failed; the previous recommendations are kept."""


@dataclass
class OwnedBook:
    title: str
    asin: str | None
    added_at: int
    series: list[tuple[str, str | None]]  # (series name, sequence)


@dataclass
class _Library:
    asins: set[str]
    titles: set[str]

    def owns(self, product: dict) -> bool:
        return (
            product.get("asin") in self.asins
            or title_key(product.get("title") or "") in self.titles
        )


@dataclass
class _AbsSeries:
    name: str
    members: list[tuple[OwnedBook, float | None]] = field(default_factory=list)


@dataclass
class _TrackedSeries:
    title: str
    seed_asin: str
    owned_up_to: float
    rank: int


@dataclass
class _Candidate:
    product: dict
    score: float = 0.0
    because: list[str] = field(default_factory=list)


def title_key(title: str) -> str:
    """Normalized title for matching editions: ignores case, spacing, bracketed labels
    such as "(Unabridged)" and trailing " - Publisher" suffixes."""
    stripped = _DASH_SUFFIX_RE.sub("", _BRACKETED_RE.sub("", title).strip())
    return " ".join(stripped.lower().split())


def _sequence_number(value: str | None) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None  # ranges like "1-3", omnibus labels, etc.


def _format_sequence(value: float) -> str:
    return str(int(value)) if value.is_integer() else str(value)


def _parse_series(metadata: dict) -> list[tuple[str, str | None]]:
    # A single expanded item carries a structured list; the library items listing
    # flattens it to a string like "The Empyrean #2, Other Series #1".
    structured = metadata.get("series")
    if isinstance(structured, list):
        return [(s["name"], s.get("sequence") or None) for s in structured if s.get("name")]

    series: list[tuple[str, str | None]] = []
    for part in (metadata.get("seriesName") or "").split(", "):
        name, sep, sequence = part.rpartition(" #")
        if not sep:
            name, sequence = part, ""
        if name.strip():
            series.append((name.strip(), sequence.strip() or None))
    return series


def owned_books_from_items(items: list[dict]) -> list[OwnedBook]:
    owned: list[OwnedBook] = []
    for item in items:
        metadata = (item.get("media") or {}).get("metadata") or {}
        title = metadata.get("title")
        if not title:
            continue
        owned.append(
            OwnedBook(
                title=title,
                asin=metadata.get("asin") or None,
                added_at=item.get("addedAt") or 0,
                series=_parse_series(metadata),
            )
        )
    return owned


class _Audible:
    """Wraps AudibleClient with a concurrency cap and per-call error isolation, so one
    failing title doesn't abort the refresh."""

    def __init__(self, client: AudibleClient) -> None:
        self.client = client
        self._semaphore = asyncio.Semaphore(_AUDIBLE_CONCURRENCY)
        self.calls = 0
        self.failures = 0

    async def product(self, asin: str) -> dict | None:
        async with self._semaphore:
            self.calls += 1
            try:
                return await self.client.get_product(asin)
            except Exception:
                self.failures += 1
                logger.exception("Audible product lookup failed for %s", asin)
                return None

    async def similar(self, asin: str, similarity_type: str, num_results: int) -> list[dict]:
        async with self._semaphore:
            self.calls += 1
            try:
                return await self.client.similar_products(asin, similarity_type, num_results)
            except Exception:
                self.failures += 1
                logger.exception("Audible %s lookup failed for %s", similarity_type, asin)
                return []


def _is_recommendable(product: dict, library: _Library, seen: set[str]) -> bool:
    title = product.get("title")
    if not product.get("asin") or not title:
        return False
    if not is_english(product.get("language")):
        return False
    delivery = product.get("content_delivery_type")
    if delivery is not None and delivery not in _BOOK_DELIVERY_TYPES:
        return False
    if _ADAPTATION_RE.search(title) or _COLLECTION_RE.search(title):
        return False
    return not library.owns(product) and title_key(title) not in seen


def _build(
    audible: AudibleClient,
    product: dict,
    kind: RecommendationKind,
    reason: str,
    score: float,
    series: tuple[str | None, str | None] | None = None,
) -> Recommendation:
    if series is None:
        listed = product.get("series") or []
        # Prefer a numbered series over an umbrella one like "The Cosmere".
        best = next((s for s in listed if s.get("sequence")), listed[0] if listed else {})
        series = (best.get("title"), best.get("sequence") or None)

    authors = [a["name"] for a in product.get("authors") or [] if a.get("name")]
    release_date = parse_date(product.get("release_date"))
    if release_date is not None and release_date.year >= _PLACEHOLDER_YEAR:
        release_date = None
    return Recommendation(
        kind=kind,
        asin=product["asin"],
        title=product["title"],
        author_name=authors[0] if authors else None,
        cover_url=(product.get("product_images") or {}).get("500"),
        release_date=release_date,
        series=series[0],
        series_sequence=series[1],
        url=audible.product_url(product["asin"]),
        reason=reason,
        score=score,
    )


def _match_audible_series(product: dict | None, name: str, sequence: float | None) -> dict | None:
    """Which of an owned book's Audible series corresponds to its Audiobookshelf series."""
    if product is None:
        return None
    numbered = [
        s
        for s in product.get("series") or []
        if s.get("asin") and _sequence_number(s.get("sequence")) is not None
    ]
    for entry in numbered:
        if title_key(entry.get("title") or "") == title_key(name):
            return entry
    if sequence is not None:
        for entry in numbered:
            if _sequence_number(entry.get("sequence")) == sequence:
                return entry
    return numbered[0] if len(numbered) == 1 else None


async def _next_in_series(
    audible: _Audible, owned: list[OwnedBook], library: _Library, seen: set[str]
) -> list[Recommendation]:
    groups: dict[str, _AbsSeries] = {}
    for book in owned:
        for name, raw_sequence in book.series:
            group = groups.setdefault(name.lower(), _AbsSeries(name))
            group.members.append((book, _sequence_number(raw_sequence)))

    # Most recently added-to series first, one seed (the furthest-along owned book that has
    # an ASIN) per series.
    ordered = sorted(
        groups.values(), key=lambda g: max(b.added_at for b, _ in g.members), reverse=True
    )
    seeds: list[tuple[_AbsSeries, OwnedBook, float | None]] = []
    for group in ordered:
        with_asin = [(b, s) for b, s in group.members if b.asin]
        if with_asin:
            book, number = max(with_asin, key=lambda m: m[1] if m[1] is not None else -1.0)
            seeds.append((group, book, number))
        if len(seeds) >= _MAX_SERIES:
            break

    products = await asyncio.gather(*(audible.product(book.asin or "") for _, book, _ in seeds))

    tracked: dict[str, _TrackedSeries] = {}
    for rank, ((group, book, number), product) in enumerate(zip(seeds, products, strict=True)):
        entry = _match_audible_series(product, group.name, number)
        if entry is None:
            continue
        owned_numbers = [s for _, s in group.members if s is not None]
        owned_numbers.append(_sequence_number(entry["sequence"]) or 0.0)
        state = tracked.get(entry["asin"])
        if state is None:
            tracked[entry["asin"]] = _TrackedSeries(
                title=entry.get("title") or group.name,
                seed_asin=book.asin or "",
                owned_up_to=max(owned_numbers),
                rank=rank,
            )
        else:
            # Two Audiobookshelf series that are really one Audible series.
            state.owned_up_to = max(state.owned_up_to, *owned_numbers)

    series_ids = list(tracked)
    results = await asyncio.gather(
        *(audible.similar(tracked[sid].seed_asin, "InTheSameSeries", 50) for sid in series_ids)
    )

    recommendations: list[Recommendation] = []
    for series_id, products_in_series in zip(series_ids, results, strict=True):
        state = tracked[series_id]
        numbered: list[tuple[float, dict, str]] = []
        for product in products_in_series:
            for entry in product.get("series") or []:
                number_in_series = _sequence_number(entry.get("sequence"))
                if entry.get("asin") == series_id and number_in_series is not None:
                    numbered.append((number_in_series, product, entry["sequence"]))

        # Audiobookshelf often has no sequence numbers for a series, so also count the
        # Audible numbering of any book in it the library already owns.
        owned_in_series = [n for n, product, _ in numbered if library.owns(product)]
        owned_up_to = max([state.owned_up_to, *owned_in_series])
        later = [
            c for c in numbered if c[0] > owned_up_to and _is_recommendable(c[1], library, seen)
        ]
        if not later:
            continue

        # Prefer the next main entry over an in-between novella (#2.5), unless novellas
        # are all that's left.
        whole = [c for c in later if c[0].is_integer()]
        _, product, sequence = min(whole or later, key=lambda c: c[0])
        seen.add(title_key(product["title"]))
        recommendations.append(
            _build(
                audible.client,
                product,
                RecommendationKind.NEXT_IN_SERIES,
                f"Next in {state.title} — you have up to #{_format_sequence(owned_up_to)}",
                score=float(len(seeds) - state.rank),
                series=(state.title, sequence),
            )
        )
    return recommendations


def _because(titles: list[str]) -> str:
    if len(titles) == 1:
        return f"Because you have {titles[0]}"
    if len(titles) == 2:
        return f"Because you have {titles[0]} and {titles[1]}"
    return f"Because you have {titles[0]}, {titles[1]} and {len(titles) - 2} more"


async def _similar(
    audible: _Audible, owned: list[OwnedBook], library: _Library, seen: set[str]
) -> list[Recommendation]:
    seeds = sorted((b for b in owned if b.asin), key=lambda b: b.added_at, reverse=True)
    seeds = seeds[:_SIMILAR_SEEDS]
    results = await asyncio.gather(
        *(audible.similar(b.asin or "", "RawSimilarities", _SIMILAR_PER_SEED) for b in seeds)
    )

    candidates: dict[str, _Candidate] = {}
    for seed, products in zip(seeds, results, strict=True):
        for rank, product in enumerate(products):
            if not _is_recommendable(product, library, seen):
                continue
            candidate = candidates.setdefault(title_key(product["title"]), _Candidate(product))
            # Every suggesting book counts ~1, with Audible's own ordering as a tiebreaker.
            candidate.score += 1 - rank / (_SIMILAR_PER_SEED * 2)
            if seed.title not in candidate.because:
                candidate.because.append(seed.title)

    ranked: list[_Candidate] = []
    per_author: dict[str, int] = {}
    for candidate in sorted(candidates.values(), key=lambda c: c.score, reverse=True):
        authors = candidate.product.get("authors") or [{}]
        author = (authors[0].get("name") or "").lower()
        if per_author.get(author, 0) >= _MAX_SIMILAR_PER_AUTHOR:
            continue
        per_author[author] = per_author.get(author, 0) + 1
        ranked.append(candidate)
        if len(ranked) >= _MAX_SIMILAR:
            break
    return [
        _build(
            audible.client,
            c.product,
            RecommendationKind.SIMILAR,
            _because(c.because),
            score=round(c.score, 3),
        )
        for c in ranked
    ]


def list_recommendations(db: Session) -> list[Recommendation]:
    return db.query(Recommendation).order_by(Recommendation.score.desc()).all()


async def refresh_recommendations(db: Session) -> list[Recommendation]:
    """Rebuild the shared recommendation list from the Audiobookshelf library.

    Raises ``RuntimeError`` if Audiobookshelf is not configured, and
    ``AudibleUnavailableError`` if every Audible lookup failed (the existing rows are kept
    rather than being replaced with an empty list).
    """
    owned = owned_books_from_items(await AudiobookshelfClient().list_library_items())
    library = _Library(
        asins={b.asin for b in owned if b.asin},
        titles={title_key(b.title) for b in owned},
    )
    audible = _Audible(AudibleClient())
    seen: set[str] = set()

    # Series first, so a title that is both "next in series" and "similar" shows as the former.
    recommendations = await _next_in_series(audible, owned, library, seen)
    recommendations += await _similar(audible, owned, library, seen)

    if audible.calls and audible.failures == audible.calls:
        raise AudibleUnavailableError("All Audible lookups failed")

    db.query(Recommendation).delete()
    db.add_all(recommendations)
    db.commit()
    logger.info("Built %d recommendations from %d library items", len(recommendations), len(owned))
    return list_recommendations(db)
