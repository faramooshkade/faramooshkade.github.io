# فراموشکده — faramooshkade.github.io

The website of **فراموشکده**, a Persian-language book club that meets every
Thursday at 18:00. The site is a single static page that collects the handouts,
booklists and printables we make for the meetings, plus the list of books we
have already read together.

Live at <https://faramooshkade.github.io>.

## What is here

Everything is plain, hand-written HTML — no build step, no framework, no
dependencies. `index.html` carries its own CSS inline and links to the files
next to it.

| Section on the page | Files |
| --- | --- |
| کتاب‌هایی که خوانده‌ایم — books we have read | generated into `index.html` between the `READ-BOOKS` markers |
| کتابِ بعدی را انتخاب کنیم — booklist to vote on | `booklist.{html,pdf}`, `booklist-en.{html,pdf}` |
| دفترچهٔ نویسندگان — author notes | `chekhov.{html,pdf,txt}`, `chekhov-en.{html,pdf}`, `camus.{html,pdf,txt}`, `camus-importance.{html,pdf,txt}` |
| معرفی و دعوت — print material | `tabligh/` (poster, invitation cards, bookmark) and `advertisement.png` |

Each handout exists in Persian and, where it makes sense, in English; PDFs are
the print-ready versions of the matching HTML.

## The books-we-have-read section

That section is **generated**, not edited by hand. `update_books.py` reads the
Jekyll posts of the sibling repo [`travel-in-books.github.io`][tib], keeps the
ones tagged «فراموشکده», and rewrites the block between

```html
<!-- READ-BOOKS:START -->  …  <!-- READ-BOOKS:END -->
```

in `index.html` with one card per book, newest first. Title, author, country,
year, page count and rating come from the table at the top of each post; the
cover image and the permalink come from the front matter.

```bash
./update_books.py --dry-run   # print the generated block, change nothing
./update_books.py             # rewrite index.html in place
```

It expects the posts at `../travel-in-books.github.io/_posts`. Point it
elsewhere with `--posts-dir`, or change the tag with `--tag`. Python 3, no
third-party packages.

So: to add a book, publish the post in the other repo, tag it «فراموشکده», then
re-run the script here and commit the result.

[tib]: https://travel-in-books.github.io

## Editing the rest

Open `index.html` and edit the relevant `<section>`. Cards follow one shape:

```html
<article class="card green">      <!-- green | blue | red | plum | sand -->
  <h3>عنوان</h3>
  <p class="sub">زیرعنوان</p>
  <p>توضیح</p>
  <ul class="files">
    <li><a href="file.pdf"><span class="lat">PDF</span></a></li>
  </ul>
</article>
```

The page is right-to-left; wrap Latin text (`PDF`, `English`, `A5`) in
`<span class="lat">` so it stays readable inside a Persian line.

## Publishing

GitHub Pages serves the `main` branch from the repository root — pushing to
`main` is the deploy. To preview locally, open `index.html` in a browser, or
run `python3 -m http.server` and visit <http://localhost:8000>.
