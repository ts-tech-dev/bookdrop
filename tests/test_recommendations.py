import asyncio

import pytest

from app.models import Recommendation
from app.models.enums import RecommendationKind
from app.services import audible, audiobookshelf
from app.services.recommendations import owned_books_from_items, refresh_recommendations


def _run(coro):
    return asyncio.run(coro)


def _item(title, asin=None, series=None, added_at=0):
    return {
        "addedAt": added_at,
        "media": {"metadata": {"title": title, "asin": asin, "seriesName": series}},
    }


def _product(asin, title, author="Some Author", series=None, **extra):
    return {
        "asin": asin,
        "title": title,
        "authors": [{"name": author}],
        "language": "english",
        "content_delivery_type": "MultiPartBook",
        "series": [
            {"asin": sid, "title": name, "sequence": seq} for sid, name, seq in (series or [])
        ],
        "product_images": {"500": f"https://img/{asin}.jpg"},
        **extra,
    }


@pytest.fixture()
def fake_sources(monkeypatch):
    """Stub the Audiobookshelf library and Audible lookups with controllable data."""
    state: dict = {"items": [], "products": {}, "sims": {}, "fail": False}

    async def _items(self):
        return list(state["items"])

    async def _get_product(self, asin):
        if state["fail"]:
            raise RuntimeError("boom")
        return state["products"].get(asin)

    async def _similar(self, asin, similarity_type, num_results=20):
        if state["fail"]:
            raise RuntimeError("boom")
        return list(state["sims"].get((asin, similarity_type), []))

    monkeypatch.setattr(audiobookshelf.AudiobookshelfClient, "list_library_items", _items)
    monkeypatch.setattr(audible.AudibleClient, "get_product", _get_product)
    monkeypatch.setattr(audible.AudibleClient, "similar_products", _similar)
    return state


def test_owned_books_parses_flattened_series_names():
    owned = owned_books_from_items(
        [_item("Iron Flame", "A2", "The Empyrean #2, Side Stories #0.5"), _item("No Series")]
    )

    assert owned[0].series == [("The Empyrean", "2"), ("Side Stories", "0.5")]
    assert owned[1].series == []


def test_next_in_series_merges_renamed_series_and_skips_novellas(db_session, fake_sources):
    # Audiobookshelf calls book 1 "Fourth Wing" and book 2 "The Empyrean"; Audible knows
    # both as series S1, so the next book is #3, not #2.
    fake_sources["items"] = [
        _item("Fourth Wing", "A1", "Fourth Wing #1", added_at=1),
        _item("Iron Flame", "A2", "The Empyrean #2", added_at=2),
    ]
    empyrean = [("S1", "The Empyrean", "2")]
    fake_sources["products"] = {
        "A1": _product("A1", "Fourth Wing", series=[("S1", "The Empyrean", "1")]),
        "A2": _product("A2", "Iron Flame", series=empyrean),
    }
    in_series = [
        _product("A1-alt", "Fourth Wing", series=[("S1", "The Empyrean", "1")]),  # owned title
        _product("A25", "Novella", series=[("S1", "The Empyrean", "2.5")]),
        _product(
            "A3-drama", "Onyx Storm (Dramatized Adaptation)", series=[("S1", "The Empyrean", "3")]
        ),
        _product("A4", "Book Four", series=[("S1", "The Empyrean", "4")]),
        _product("A3", "Onyx Storm", series=[("S1", "The Empyrean", "3")]),
    ]
    fake_sources["sims"] = {
        ("A1", "InTheSameSeries"): in_series,
        ("A2", "InTheSameSeries"): in_series,
    }

    recs = _run(refresh_recommendations(db_session))

    series_recs = [r for r in recs if r.kind == RecommendationKind.NEXT_IN_SERIES]
    assert [(r.title, r.series, r.series_sequence) for r in series_recs] == [
        ("Onyx Storm", "The Empyrean", "3")
    ]
    assert series_recs[0].reason == "Next in The Empyrean — you have up to #2"
    assert series_recs[0].url == "https://www.audible.com/pd/A3"


def test_next_in_series_falls_back_to_novella_when_nothing_else(db_session, fake_sources):
    fake_sources["items"] = [_item("Book Two", "B2", "Saga #2")]
    fake_sources["products"] = {"B2": _product("B2", "Book Two", series=[("S", "Saga", "2")])}
    fake_sources["sims"] = {
        ("B2", "InTheSameSeries"): [_product("B25", "Interlude", series=[("S", "Saga", "2.5")])]
    }

    recs = _run(refresh_recommendations(db_session))

    assert [r.title for r in recs] == ["Interlude"]


def test_similar_ranks_by_how_many_books_suggest_it(db_session, fake_sources):
    fake_sources["items"] = [
        _item("Owned One", "O1", added_at=1),
        _item("Owned Two", "O2", added_at=2),
        _item("Owned Three", None, added_at=3),  # no ASIN: can't seed, but counts as owned
    ]
    fake_sources["sims"] = {
        ("O1", "RawSimilarities"): [
            _product("X1", "Popular Pick"),
            _product("X2", "Owned Three (Unabridged)"),
            _product("X3", "Podcast Thing", content_delivery_type="Podcast"),
            _product("X4", "Livre", language="french"),
        ],
        ("O2", "RawSimilarities"): [
            _product("X5", "Single Pick"),
            _product("X1-alt", "Popular Pick"),  # another edition of the same title
            _product("O1", "Owned One"),
        ],
    }

    recs = _run(refresh_recommendations(db_session))

    assert [r.title for r in recs] == ["Popular Pick", "Single Pick"]
    assert recs[0].kind == RecommendationKind.SIMILAR
    assert recs[0].reason == "Because you have Owned Two and Owned One"
    assert recs[1].reason == "Because you have Owned Two"


def test_refresh_replaces_previous_rows(db_session, fake_sources):
    fake_sources["items"] = [_item("Seed", "S")]
    fake_sources["sims"] = {("S", "RawSimilarities"): [_product("X", "First")]}
    _run(refresh_recommendations(db_session))

    fake_sources["sims"] = {("S", "RawSimilarities"): [_product("Y", "Second")]}
    _run(refresh_recommendations(db_session))

    assert [r.title for r in db_session.query(Recommendation).all()] == ["Second"]


def test_refresh_keeps_old_rows_when_audible_is_down(db_session, fake_sources):
    fake_sources["items"] = [_item("Seed", "S")]
    fake_sources["sims"] = {("S", "RawSimilarities"): [_product("X", "Keep Me")]}
    _run(refresh_recommendations(db_session))

    fake_sources["fail"] = True
    with pytest.raises(Exception, match="All Audible lookups failed"):
        _run(refresh_recommendations(db_session))

    assert [r.title for r in db_session.query(Recommendation).all()] == ["Keep Me"]


def test_recommendations_endpoints(client, fake_sources):
    fake_sources["items"] = [_item("Seed", "S")]
    fake_sources["sims"] = {("S", "RawSimilarities"): [_product("X", "Pick", author="Jane Writer")]}

    assert client.get("/recommendations").json() == []

    refreshed = client.post("/recommendations/refresh")
    assert refreshed.status_code == 200
    assert [(r["title"], r["author_name"]) for r in refreshed.json()] == [("Pick", "Jane Writer")]
    assert [r["title"] for r in client.get("/recommendations").json()] == ["Pick"]


def test_refresh_endpoint_error_codes(client, fake_sources, monkeypatch):
    fake_sources["items"] = [_item("Seed", "S")]
    fake_sources["fail"] = True
    assert client.post("/recommendations/refresh").status_code == 502

    async def _unconfigured(self):
        raise RuntimeError("Audiobookshelf is not configured")

    monkeypatch.setattr(audiobookshelf.AudiobookshelfClient, "list_library_items", _unconfigured)
    res = client.post("/recommendations/refresh")
    assert res.status_code == 400
    assert res.json()["detail"] == "Audiobookshelf is not configured"


def test_next_in_series_uses_audible_numbering_for_unnumbered_owned_books(db_session, fake_sources):
    # Audiobookshelf only knows book 1's number; books 2 and 3 are owned (one under a
    # "[Dramatized Adaptation] - GraphicAudio" title) but unnumbered.
    fake_sources["items"] = [
        _item("Magic Bites", "M1", "Kate Daniels #1"),
        _item("Magic Burns", None, "Kate Daniels"),
        _item("Magic Strikes [Dramatized Adaptation] - GraphicAudio", None, "Kate Daniels"),
    ]
    kd = "Kate Daniels"
    fake_sources["products"] = {"M1": _product("M1", "Magic Bites", series=[("K", kd, "1")])}
    fake_sources["sims"] = {
        ("M1", "InTheSameSeries"): [
            _product("M2", "Magic Burns", series=[("K", kd, "2")]),
            _product("M3", "Magic Strikes", series=[("K", kd, "3")]),
            _product("M4", "Magic Bleeds", series=[("K", kd, "4")]),
        ]
    }

    recs = _run(refresh_recommendations(db_session))

    assert [(r.title, r.reason) for r in recs] == [
        ("Magic Bleeds", "Next in Kate Daniels — you have up to #3")
    ]


def test_similar_caps_per_author_and_drops_collections_and_placeholder_dates(
    db_session, fake_sources
):
    fake_sources["items"] = [_item("Seed", "S")]
    fake_sources["sims"] = {
        ("S", "RawSimilarities"): [
            _product("P1", "Prolific One", author="Prolific"),
            _product("P2", "Prolific Two", author="Prolific"),
            _product("P3", "Prolific Three", author="Prolific"),
            _product("B1", "Saga: Books 1-3", author="Other"),
            _product("B2", "The Complete Series Box Set", author="Other"),
            _product("T1", "Someday", author="Other", release_date="2200-01-01"),
        ]
    }

    recs = _run(refresh_recommendations(db_session))

    assert [r.title for r in recs] == ["Prolific One", "Prolific Two", "Someday"]
    assert recs[2].release_date is None
