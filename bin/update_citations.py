#!/usr/bin/env python3

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests


ROOT = Path(__file__).resolve().parents[1]

BIB_FILES = [
    ROOT / "_bibliography" / "papers.bib",
    ROOT / "_bibliography" / "preprints.bib",
    ROOT / "_bibliography" / "posters.bib",
]

OUT = ROOT / "assets" / "data" / "citations.json"

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
SCHOLAR_AUTHOR_ID = os.environ.get("SCHOLAR_AUTHOR_ID", "sHQFKFUAAAAJ")


def require_api_key() -> None:
    if not SERPAPI_KEY:
        print("SERPAPI_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    if SERPAPI_KEY.strip() != SERPAPI_KEY:
        print("SERPAPI_KEY has leading/trailing whitespace.", file=sys.stderr)
        sys.exit(1)

    if SERPAPI_KEY in {"<key>", "your_serpapi_key_here", "paste_actual_key_here"}:
        print("SERPAPI_KEY is still set to a placeholder.", file=sys.stderr)
        sys.exit(1)


def clean_latex_text(value: str) -> str:
    if not value:
        return ""

    replacements = {
        r"\texttimes{}": "x",
        r"\&": "&",
        r"``": '"',
        r"''": '"',
        r"---": "-",
        r"--": "-",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"\\[a-zA-Z]+\*?", "", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def extract_field(chunk: str, field_name: str) -> Optional[str]:
    pattern = re.compile(rf"\b{re.escape(field_name)}\s*=\s*\{{", re.IGNORECASE)
    match = pattern.search(chunk)

    if not match:
        return None

    start = match.end()
    depth = 1
    i = start

    while i < len(chunk):
        char = chunk[i]

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return clean_latex_text(chunk[start:i])

        i += 1

    return None


def parse_bib_entries(text: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    chunks = re.split(r"(?=@\w+\{)", text)

    for chunk in chunks:
        header = re.match(r"@\w+\{([^,]+),", chunk.strip())
        if not header:
            continue

        key = header.group(1).strip()

        title = extract_field(chunk, "title") or ""
        author = extract_field(chunk, "author") or ""
        scholar_query = extract_field(chunk, "scholar_query") or ""
        scholar_url = extract_field(chunk, "scholar_url") or ""
        doi = extract_field(chunk, "doi") or ""
        arxiv = extract_field(chunk, "arxiv") or extract_field(chunk, "eprint") or ""

        if scholar_query:
            query = scholar_query
        elif title and author:
            query = f"{title} {author}"
        elif title:
            query = title
        else:
            print(f"Skipping {key}: no title or scholar_query.", file=sys.stderr)
            continue

        entries.append(
            {
                "key": key,
                "title": title,
                "author": author,
                "query": query,
                "scholar_url": scholar_url,
                "doi": doi,
                "arxiv": arxiv,
            }
        )

    return entries


def normalize_for_pattern(value: str) -> str:
    value = clean_latex_text(value or "")
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def pattern_tokens(value: str) -> Set[str]:
    tokens = set(normalize_for_pattern(value).split())

    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "using",
        "via",
    }

    return tokens - stopwords


def significant_tokens(value: str) -> Set[str]:
    tokens = set(normalize_for_pattern(value).split())

    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "using",
        "via",
    }

    return tokens - stopwords


def generated_title_patterns(title: str) -> List[str]:
    title = clean_latex_text(title or "")
    patterns: List[str] = []

    full = normalize_for_pattern(title)
    if full:
        patterns.append(full)

    if ":" in title:
        subtitle = title.split(":", 1)[1].strip()
        subtitle_norm = normalize_for_pattern(subtitle)
        if subtitle_norm:
            patterns.append(subtitle_norm)

    return list(dict.fromkeys(patterns))


def pattern_match_score(pattern: str, scholar_title: str) -> float:
    p_tokens = pattern_tokens(pattern)
    s_tokens = pattern_tokens(scholar_title)

    if not p_tokens or not s_tokens:
        return 0.0

    return len(p_tokens & s_tokens) / len(p_tokens)


def title_overlap_score(expected: str, actual: str) -> float:
    expected_tokens = significant_tokens(expected)
    actual_tokens = significant_tokens(actual)

    if not expected_tokens or not actual_tokens:
        return 0.0

    return len(expected_tokens & actual_tokens) / len(expected_tokens | actual_tokens)


def title_inclusion_score(expected: str, actual: str) -> float:
    expected_tokens = significant_tokens(expected)
    actual_tokens = significant_tokens(actual)

    if not expected_tokens or not actual_tokens:
        return 0.0

    return len(expected_tokens & actual_tokens) / len(expected_tokens)


def title_containment_score(expected: str, actual: str) -> float:
    expected_tokens = significant_tokens(expected)
    actual_tokens = significant_tokens(actual)

    if not expected_tokens or not actual_tokens:
        return 0.0

    intersection = len(expected_tokens & actual_tokens)

    return max(
        intersection / len(expected_tokens),
        intersection / len(actual_tokens),
    )


def split_subtitle(value: str) -> Optional[str]:
    if ":" not in value:
        return None

    return value.split(":", 1)[1].strip()


def shared_subtitle_score(expected: str, actual: str) -> float:
    expected_subtitle = split_subtitle(expected)
    actual_subtitle = split_subtitle(actual)

    if not expected_subtitle or not actual_subtitle:
        return 0.0

    return pattern_match_score(expected_subtitle, actual_subtitle)


def extract_system_name(value: str) -> str:
    if ":" not in value:
        return ""

    return normalize_for_pattern(value.split(":", 1)[0]).strip()


def looks_like_renamed_same_work(expected: str, actual: str) -> bool:
    expected_subtitle = split_subtitle(expected)
    actual_subtitle = split_subtitle(actual)

    if not expected_subtitle or not actual_subtitle:
        return False

    subtitle_score = pattern_match_score(expected_subtitle, actual_subtitle)
    reverse_subtitle_score = pattern_match_score(actual_subtitle, expected_subtitle)

    expected_system = extract_system_name(expected)
    actual_system = extract_system_name(actual)

    different_system_name = (
        expected_system
        and actual_system
        and expected_system != actual_system
    )

    return (
        different_system_name
        and subtitle_score >= 0.80
        and reverse_subtitle_score >= 0.80
    )


def is_likely_same_work(expected_title: str, scholar_title: str) -> bool:
    jaccard = title_overlap_score(expected_title, scholar_title)
    inclusion = title_inclusion_score(expected_title, scholar_title)
    containment = title_containment_score(expected_title, scholar_title)
    subtitle = shared_subtitle_score(expected_title, scholar_title)
    renamed = looks_like_renamed_same_work(expected_title, scholar_title)

    patterns = generated_title_patterns(expected_title)
    best_pattern_score = 0.0

    for pattern in patterns:
        best_pattern_score = max(
            best_pattern_score,
            pattern_match_score(pattern, scholar_title),
        )

    return (
        jaccard >= 0.55
        or inclusion >= 0.70
        or containment >= 0.75
        or subtitle >= 0.80
        or renamed
        or best_pattern_score >= 0.80
    )


def cited_by_value_from_author_article(article: Dict[str, object]) -> int:
    cited_by = article.get("cited_by")

    if isinstance(cited_by, dict):
        value = cited_by.get("value")
        if isinstance(value, int):
            return value

    if isinstance(cited_by, int):
        return cited_by

    return 0


def cited_by_link_from_author_article(article: Dict[str, object]) -> str:
    cited_by = article.get("cited_by")

    if isinstance(cited_by, dict):
        return cited_by.get("link", "") or ""

    return ""


def fetch_author_profile_articles() -> List[Dict[str, object]]:
    if not SCHOLAR_AUTHOR_ID:
        return []

    articles: List[Dict[str, object]] = []
    start = 0

    while True:
        params = {
            "engine": "google_scholar_author",
            "author_id": SCHOLAR_AUTHOR_ID,
            "api_key": SERPAPI_KEY,
            "num": "100",
            "start": str(start),
        }

        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=30,
        )

        if response.status_code != 200:
            print("SerpApi author status:", response.status_code, file=sys.stderr)
            print("SerpApi author body:", response.text, file=sys.stderr)

        response.raise_for_status()
        data = response.json()

        page_articles = data.get("articles", []) or []
        articles.extend(page_articles)

        if len(page_articles) < 100:
            break

        start += 100
        time.sleep(1.0)

    return articles


def normalize_author_article(article: Dict[str, object]) -> Dict[str, object]:
    return {
        "matched_title": article.get("title", "") or "",
        "publication_info_summary": article.get("publication", "") or "",
        "year": article.get("year", "") or "",
        "cited_by": cited_by_value_from_author_article(article),
        "scholar_link": cited_by_link_from_author_article(article)
        or article.get("link", "")
        or "",
        "citation_id": article.get("citation_id", "") or "",
        "source": "google_scholar_author_profile",
    }


def fetch_matching_author_profile_rows(
    entry: Dict[str, str],
    author_articles: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    expected_title = entry.get("title") or entry["query"]
    patterns = generated_title_patterns(expected_title)

    rows: List[Dict[str, object]] = []

    for article in author_articles:
        row = normalize_author_article(article)
        scholar_title = str(row["matched_title"])

        best_pattern = ""
        best_pattern_score = 0.0

        for pattern in patterns:
            score = pattern_match_score(pattern, scholar_title)
            if score > best_pattern_score:
                best_pattern_score = score
                best_pattern = pattern

        jaccard = title_overlap_score(expected_title, scholar_title)
        inclusion = title_inclusion_score(expected_title, scholar_title)
        containment = title_containment_score(expected_title, scholar_title)
        subtitle = shared_subtitle_score(expected_title, scholar_title)
        renamed = looks_like_renamed_same_work(expected_title, scholar_title)

        is_match = (
            is_likely_same_work(expected_title, scholar_title)
            or best_pattern_score >= 0.80
        )

        if is_match:
            row["matched_pattern"] = best_pattern
            row["scores"] = {
                "pattern": round(best_pattern_score, 3),
                "jaccard": round(jaccard, 3),
                "inclusion": round(inclusion, 3),
                "containment": round(containment, 3),
                "subtitle": round(subtitle, 3),
                "renamed_same_work": renamed,
            }
            rows.append(row)

    return rows


def regular_scholar_row_dedupe_key(row: Dict[str, object]) -> str:
    title = str(row.get("matched_title") or "").strip()
    venue = str(row.get("publication_info_summary") or "").strip()
    cited_by = str(row.get("cited_by") or "").strip()

    return normalize_for_pattern(f"{title} {venue} {cited_by}")


def fetch_regular_scholar_rows(
    query: str,
    expected_title: str,
) -> List[Dict[str, object]]:
    params = {
        "engine": "google_scholar",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": "20",
        "as_sdt": "0,5",
    }

    response = requests.get(
        "https://serpapi.com/search.json",
        params=params,
        timeout=30,
    )

    if response.status_code != 200:
        print("SerpApi regular status:", response.status_code, file=sys.stderr)
        print("SerpApi regular body:", response.text, file=sys.stderr)

    response.raise_for_status()
    data = response.json()

    rows: List[Dict[str, object]] = []
    patterns = generated_title_patterns(expected_title)

    for result in data.get("organic_results", []):
        scholar_title = result.get("title", "") or ""

        inline_links = result.get("inline_links", {}) or {}
        cited_by = inline_links.get("cited_by", {}) or {}
        versions = inline_links.get("versions", {}) or {}
        publication_info = result.get("publication_info", {}) or {}

        count = cited_by.get("total")
        if not isinstance(count, int):
            count = 0

        link = cited_by.get("link") or result.get("link") or ""

        best_pattern = ""
        best_pattern_score = 0.0

        for pattern in patterns:
            score = pattern_match_score(pattern, scholar_title)
            if score > best_pattern_score:
                best_pattern_score = score
                best_pattern = pattern

        jaccard = title_overlap_score(expected_title, scholar_title)
        inclusion = title_inclusion_score(expected_title, scholar_title)
        containment = title_containment_score(expected_title, scholar_title)
        subtitle = shared_subtitle_score(expected_title, scholar_title)
        renamed = looks_like_renamed_same_work(expected_title, scholar_title)

        is_match = (
            is_likely_same_work(expected_title, scholar_title)
            or best_pattern_score >= 0.80
        )

        if is_match:
            rows.append(
                {
                    "matched_title": scholar_title,
                    "publication_info_summary": publication_info.get("summary", "") or "",
                    "year": "",
                    "cited_by": count,
                    "scholar_link": link,
                    "versions_total": versions.get("total"),
                    "matched_pattern": best_pattern,
                    "source": "regular_google_scholar_search",
                    "scores": {
                        "pattern": round(best_pattern_score, 3),
                        "jaccard": round(jaccard, 3),
                        "inclusion": round(inclusion, 3),
                        "containment": round(containment, 3),
                        "subtitle": round(subtitle, 3),
                        "renamed_same_work": renamed,
                    },
                }
            )

    return rows


def build_author_profile_result(
    entry: Dict[str, str],
    author_articles: List[Dict[str, object]],
) -> Optional[Dict[str, object]]:
    rows = fetch_matching_author_profile_rows(entry, author_articles)

    if not rows:
        return None

    seen = set()
    deduped_rows: List[Dict[str, object]] = []

    for row in rows:
        # Keep separate Google Scholar profile rows distinct.
        dedupe_key = row.get("citation_id") or regular_scholar_row_dedupe_key(row)

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        deduped_rows.append(row)

    if not deduped_rows:
        return None

    total = sum(int(row.get("cited_by") or 0) for row in deduped_rows)
    best_row = max(deduped_rows, key=lambda row: int(row.get("cited_by") or 0))

    return {
        "cited_by": total,
        "scholar_link": best_row.get("scholar_link", ""),
        "matched_title": best_row.get("matched_title", ""),
        "scholar_rows": deduped_rows,
        "counting_method": "sum_matching_google_scholar_author_profile_rows",
    }


def build_regular_scholar_result(entry: Dict[str, str]) -> Dict[str, object]:
    query = entry["query"]
    expected_title = entry.get("title") or query

    rows = fetch_regular_scholar_rows(
        query=query,
        expected_title=expected_title,
    )

    seen = set()
    deduped_rows: List[Dict[str, object]] = []

    for row in rows:
        dedupe_key = regular_scholar_row_dedupe_key(row)

        if not dedupe_key:
            continue

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        deduped_rows.append(row)

    total = sum(int(row.get("cited_by") or 0) for row in deduped_rows)

    best_row = None
    if deduped_rows:
        best_row = max(deduped_rows, key=lambda row: int(row.get("cited_by") or 0))

    return {
        "cited_by": total if deduped_rows else None,
        "scholar_link": best_row.get("scholar_link", "") if best_row else "",
        "matched_title": best_row.get("matched_title", "") if best_row else "",
        "scholar_rows": deduped_rows,
        "counting_method": "sum_matching_regular_google_scholar_rows",
    }


def main() -> None:
    require_api_key()

    all_entries: List[Dict[str, str]] = []

    for bib_file in BIB_FILES:
        if not bib_file.exists():
            print(f"Skipping missing file: {bib_file}", file=sys.stderr)
            continue

        entries = parse_bib_entries(bib_file.read_text(encoding="utf-8"))
        print(f"Found {len(entries)} entries in {bib_file.relative_to(ROOT)}")
        all_entries.extend(entries)

    print(f"\nFetching Google Scholar author profile: {SCHOLAR_AUTHOR_ID}")
    author_articles = fetch_author_profile_articles()

    if author_articles:
        print(f"Fetched {len(author_articles)} author-profile articles.")
    else:
        print("No author-profile articles fetched; using regular Scholar search only.")

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    citation_data: Dict[str, object] = {}

    for entry in all_entries:
        key = entry["key"]
        query = entry["query"]
        title = entry.get("title") or query

        print(f"\nLooking up: {key}")
        print(f"Title: {title}")
        print(f"Query: {query}")
        print(f"Generated patterns: {generated_title_patterns(title)}")

        try:
            result = None

            if author_articles:
                result = build_author_profile_result(entry, author_articles)

            if result is None:
                result = build_regular_scholar_result(entry)

            citation_data[key] = {
                "cited_by": result["cited_by"],
                "scholar_link": result["scholar_link"] or entry.get("scholar_url") or "",
                "matched_title": result["matched_title"],
                "scholar_rows": result["scholar_rows"],
                "counting_method": result["counting_method"],
                "query": query,
                "title": entry.get("title") or "",
                "doi": entry.get("doi") or "",
                "arxiv": entry.get("arxiv") or "",
                "updated_at": now,
            }

            print(f"{key}: {result['cited_by']} [{result['counting_method']}]")

            for row in result["scholar_rows"]:
                print(
                    "  - "
                    f"{row.get('matched_title')} | "
                    f"citations={row.get('cited_by')} | "
                    f"source={row.get('source')} | "
                    f"pattern={row.get('matched_pattern')} | "
                    f"scores={row.get('scores')}"
                )

            time.sleep(1.0)

        except Exception as exc:
            print(f"Failed for {key}: {exc}", file=sys.stderr)

            citation_data[key] = {
                "cited_by": None,
                "scholar_link": entry.get("scholar_url") or "",
                "matched_title": "",
                "scholar_rows": [],
                "counting_method": "failed",
                "query": query,
                "title": entry.get("title") or "",
                "doi": entry.get("doi") or "",
                "arxiv": entry.get("arxiv") or "",
                "updated_at": now,
                "error": str(exc),
            }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(citation_data, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"\nWrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()