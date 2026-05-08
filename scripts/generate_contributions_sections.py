#!/Users/fer/Documents/PYTHON/fer-at-sea.github.io/.venv/bin/python
"""Generate keyword-grouped contributions markdown from assets/FER.bib.

Rules:
- One subsection per keyword label exactly as written.
- Entries without keywords are excluded.
- Entries tagged with keyword 'exclude' (case-insensitive) are excluded entirely.
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import re
import unicodedata

import bibtexparser


ROOT = Path(__file__).resolve().parents[1]
BIB_PATH = ROOT / "assets" / "FER.bib"
OUT_PATH = ROOT / "assets" / "contributions_auto.qmd"

# Desired display order for keyword subsections.
# Any keyword not listed here is appended after these, in original appearance order.
SECTION_ORDER = [
    "Conference proceedings",
    "Conference presentations",
    "Master thesis",
    "Mentoring",
    "Reports",

]

# Author to emphasize in generated references.
TARGET_AUTHOR_LASTNAME = "garcia-gonzalez"


def clean_text(value: str) -> str:
    if not value:
        return ""

    # Unescape simple latex markers and flatten braces for display.
    value = value.replace(r"\&", "&")
    value = value.replace("{{", "").replace("}}", "")
    value = value.replace("{", "").replace("}", "")

    # Basic accent command cleanup (
    # keeps script dependency-free while avoiding raw latex in output).
    value = re.sub(r"\\['`^~\"=.Hcuvtkbdlr] ?\{?([A-Za-z])\}?", r"\1", value)
    value = re.sub(r"\\[A-Za-z]+\{([^{}]+)\}", r"\1", value)

    return " ".join(value.split()).strip()


def normalize_name_token(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^A-Za-z0-9-]", "", value)
    return value.lower()


def format_author(author_raw: str) -> str:
    author_raw = clean_text(author_raw)
    if not author_raw:
        return ""

    if "," in author_raw:
        last, first = [p.strip() for p in author_raw.split(",", 1)]
        initials = " ".join(f"{w[0]}." for w in first.split() if w)
        formatted = f"{last}, {initials}" if initials else last
        if normalize_name_token(last) == normalize_name_token(TARGET_AUTHOR_LASTNAME):
            return f"**{formatted}**"
        return formatted

    parts = author_raw.split()
    if len(parts) == 1:
        return parts[0]

    last = parts[-1]
    first = " ".join(parts[:-1])
    initials = " ".join(f"{w[0]}." for w in first.split() if w)
    formatted = f"{last}, {initials}" if initials else last
    if normalize_name_token(last) == normalize_name_token(TARGET_AUTHOR_LASTNAME):
        return f"**{formatted}**"
    return formatted


def format_authors(raw: str) -> str:
    authors = [a.strip() for a in (raw or "").split(" and ") if a.strip()]
    formatted = [format_author(a) for a in authors]
    formatted = [f for f in formatted if f]

    if not formatted:
        return ""
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def format_reference(fields: dict) -> str:
    authors = format_authors(fields.get("author", ""))
    year = clean_text(fields.get("year", "n.d.")) or "n.d."
    title = clean_text(fields.get("title", "Untitled")) or "Untitled"
    source = clean_text(fields.get("journal") or fields.get("booktitle") or fields.get("school") or "")
    doi = clean_text(fields.get("doi", ""))
    url = clean_text(fields.get("url", ""))

    parts = []
    if authors:
        parts.append(f"{authors} ({year}).")
    else:
        parts.append(f"({year}).")

    parts.append(f"*{title}*.")
    if source:
        parts.append(f"{source}.")

    link_target = ""
    link_label = ""
    if doi:
        link_target = doi if doi.startswith("http") else f"https://doi.org/{doi}"
        link_label = link_target
    elif url:
        link_target = url
        link_label = url

    if link_target:
        parts.append(f"[{link_label}]({link_target})")

    return " ".join(parts).replace("..", ".")


def generate() -> None:
    with BIB_PATH.open("r", encoding="utf-8") as bibfile:
        db = bibtexparser.load(bibfile)

    grouped: "OrderedDict[str, list[str]]" = OrderedDict()

    for entry in db.entries:
        keywords_raw = clean_text(entry.get("keywords", ""))
        if not keywords_raw:
            continue

        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        if any(k.lower() == "exclude" for k in keywords):
            continue

        ref_line = format_reference(entry)
        for kw in keywords:
            grouped.setdefault(kw, []).append(ref_line)

    lines = [
        "<!-- AUTO-GENERATED: do not edit manually. Run scripts/generate_contributions_sections.py -->",
        "",
    ]

    ordered_keywords = [k for k in SECTION_ORDER if k in grouped]
    ordered_keywords.extend(k for k in grouped.keys() if k not in ordered_keywords)

    for kw in ordered_keywords:
        refs = grouped[kw]
        lines.append(f"### {kw}")
        lines.append("")
        for ref in refs:
            lines.append(f"- {ref}")
        lines.append("")

    OUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate()
