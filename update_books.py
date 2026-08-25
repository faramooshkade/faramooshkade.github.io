#!/usr/bin/env python3
"""Collect the book-club books from the travel-in-books posts and put them in index.html.

Reads every Jekyll post in the sibling repo, keeps the ones tagged
«فراموشکده», and rewrites the block between the READ-BOOKS markers in
index.html with one card per book, newest first.

Usage:
    ./update_books.py              # update index.html in place
    ./update_books.py --dry-run    # print the generated HTML, change nothing
"""

import argparse
import html
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent

DEFAULT_POSTS = HERE / ".." / "travel-in-books.github.io" / "_posts"
DEFAULT_INDEX = HERE / "index.html"
DEFAULT_TAG = "فراموشکده"
SITE = "https://travel-in-books.github.io"

START = "<!-- READ-BOOKS:START -->"
END = "<!-- READ-BOOKS:END -->"

# Post permalink is /:categories/:year/:month/:day/:title/ and the title
# segment keeps the original capitalisation of the filename.
FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$")

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
FA_MONTHS = ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
             "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"]


def fa(value) -> str:
    """Render a value with Persian digits."""
    return str(value).translate(FA_DIGITS)


def split_front_matter(text: str):
    """Return (front matter, body). Both empty if the post has no front matter."""
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def scalar(front: str, key: str) -> str:
    m = re.search(rf"^{key}:\s*(.+?)\s*$", front, re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def listing(front: str, key: str) -> list:
    m = re.search(rf"^{key}:\s*\[(.*?)\]\s*$", front, re.M)
    if not m:
        return []
    return [item.strip() for item in m.group(1).split(",") if item.strip()]


def cover_path(front: str) -> str:
    """The path: line nested under image:."""
    m = re.search(r"^image:\s*\n(?:\s+.*\n)*?\s+path:\s*(\S+)", front, re.M)
    return m.group(1) if m else ""


def table_field(body: str, label: str) -> str:
    """Read a value out of the leading | key | value | table."""
    m = re.search(rf"^\|\s*{label}\s*\|\s*(.+?)\s*\|", body, re.M)
    if not m:
        return ""
    value = re.sub(r"\{%.*?%\}", "", m.group(1))  # drop liquid tags
    return value.strip()


def rating(tags: list) -> str:
    """Pull "8/10" out of the star tag."""
    for tag in tags:
        m = re.search(r"(\d+)\s*/\s*10", tag)
        if m:
            return f"{fa(m.group(1))}/۱۰"
    return ""


def post_url(categories: list, when: date, slug: str) -> str:
    segments = [c.lower() for c in categories] + [
        f"{when.year:04d}", f"{when.month:02d}", f"{when.day:02d}", slug
    ]
    return SITE + "/" + "/".join(quote(s) for s in segments) + "/"


def read_post(path: Path, tag: str):
    m = FILENAME_RE.match(path.name)
    if not m:
        return None

    front, body = split_front_matter(path.read_text(encoding="utf-8"))
    tags = listing(front, "tags")
    if tag not in tags:
        return None

    year, month, day, slug = m.groups()
    when = date(int(year), int(month), int(day))
    categories = listing(front, "categories")

    return {
        "title": table_field(body, "نام اثر") or scalar(front, "title"),
        "author": table_field(body, "نویسنده"),
        "country": table_field(body, "کشور"),
        "year": table_field(body, "سال چاپ"),
        "pages": table_field(body, "تعداد صفحات"),
        "rating": rating(tags),
        "cover": SITE + cover_path(front) if cover_path(front) else "",
        "url": post_url(categories, when, slug),
        "date": when,
    }


def render(books: list) -> str:
    lines = [
        START,
        f'      <p class="section-note">تا امروز {fa(len(books))} کتاب با هم خوانده‌ایم. '
        f'هر کتاب به یادداشتِ کاملش در «سفر در کتاب‌ها» پیوند دارد.</p>',
        '      <div class="grid">',
    ]

    for book in books:
        title = html.escape(book["title"])
        url = html.escape(book["url"])
        meta = " · ".join(x for x in (book["country"], book["year"], book["pages"]) if x)
        stamp = f'{FA_MONTHS[book["date"].month - 1]} {fa(book["date"].year)}'

        lines.append('        <article class="card plum book-card">')
        if book["cover"]:
            lines.append(
                f'          <a class="cover" href="{url}">'
                f'<img src="{html.escape(book["cover"])}" alt="جلد کتاب {title}" '
                f'loading="lazy" width="66" height="99"></a>'
            )
        lines.append('          <div class="book-body">')
        lines.append(f'            <h3><a href="{url}">{title}</a></h3>')
        if book["author"]:
            lines.append(f'            <p class="sub">{html.escape(book["author"])}</p>')
        if meta:
            lines.append(f'            <p class="book-meta">{html.escape(meta)}</p>')
        lines.append(
            f'            <p class="book-meta">{stamp}'
            + (f' · ⭐ {book["rating"]}' if book["rating"] else "")
            + "</p>"
        )
        lines.append("          </div>")
        lines.append("        </article>")

    lines += ["      </div>", f"      {END}"]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--posts-dir", type=Path, default=DEFAULT_POSTS)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--dry-run", action="store_true",
                        help="print the generated block instead of writing it")
    args = parser.parse_args()

    posts_dir = args.posts_dir.resolve()
    if not posts_dir.is_dir():
        print(f"posts directory not found: {posts_dir}", file=sys.stderr)
        return 1

    books = [b for b in (read_post(p, args.tag) for p in sorted(posts_dir.glob("*.md"))) if b]
    books.sort(key=lambda b: b["date"], reverse=True)

    if not books:
        print(f"no posts tagged «{args.tag}» in {posts_dir}", file=sys.stderr)
        return 1

    block = render(books)

    if args.dry_run:
        print(block)
        print(f"\n{len(books)} books found", file=sys.stderr)
        return 0

    index = args.index.resolve()
    text = index.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"markers {START} / {END} not found in {index}", file=sys.stderr)
        return 1

    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S
    )

    if updated == text:
        print(f"{index.name} already up to date ({len(books)} books)")
        return 0

    index.write_text(updated, encoding="utf-8")
    print(f"{index.name} updated with {len(books)} books:")
    for book in books:
        print(f"  {book['date']}  {book['title']} — {book['author']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
