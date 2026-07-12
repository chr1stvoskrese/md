<p align="center">
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/English-0969da?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MCAzMCI%2bPGNsaXBQYXRoIGlkPSJhIj48cGF0aCBkPSJNMCAwdjMwaDYwVjB6Ii8%2bPC9jbGlwUGF0aD48cGF0aCBkPSJNMCAwdjMwaDYwVjB6IiBmaWxsPSIjMDEyMTY5Ii8%2bPHBhdGggZD0iTTAgMGw2MCAzMG0wLTMwTDAgMzAiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSI2Ii8%2bPHBhdGggZD0iTTAgMGw2MCAzMG0wLTMwTDAgMzAiIGNsaXAtcGF0aD0idXJsKCNhKSIgc3Ryb2tlPSIjQzgxMDJFIiBzdHJva2Utd2lkdGg9IjQiLz48cGF0aCBkPSJNMzAgMHYzME0wIDE1aDYwIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMTAiLz48cGF0aCBkPSJNMzAgMHYzME0wIDE1aDYwIiBzdHJva2U9IiNDODEwMkUiIHN0cm9rZS13aWR0aD0iNiIvPjwvc3ZnPgo%3d"></a>
  <a href="README_RU.md"><img alt="Русский" src="https://img.shields.io/badge/%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-555c66?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA5IDYiPjxwYXRoIGZpbGw9IiNmZmYiIGQ9Ik0wIDBoOXYySDB6Ii8%2bPHBhdGggZmlsbD0iIzAwMzlBNiIgZD0iTTAgMmg5djJIMHoiLz48cGF0aCBmaWxsPSIjRDUyQjFFIiBkPSJNMCA0aDl2MkgweiIvPjwvc3ZnPgo%3d"></a>
</p>

<h1 align="center">md</h1>

<p align="center">
  <strong>Markdown reader for the terminal.</strong>
</p>

<p align="center">
  One file · Pure Python · Zero dependencies
</p>

---

```bash
python md.py README.md      # open a file
python md.py ~/notes        # open a folder of notes
python md.py                # current folder
```

Requires only Python 3.8+. No `pip install`.

---

## Features

- **Full Markdown rendering** — headings, lists, checkboxes, blockquotes,
  tables, horizontal rules, YAML front-matter, width-aware line wrapping.
- **Inline formatting** — bold, italic, strikethrough, `code`, highlight `==text==`.
- **Syntax-highlighted code** — Python, Bash, JavaScript/TypeScript, JSON and a
  generic fallback; framed, copy-clean blocks — no line numbers or gutter, so a
  terminal selection copies exactly the code.
- **Link navigation** — wiki-links `[[Note]]` and `[[Note|alias]]`, plus regular
  `[text](url)`. Every link gets a number — press it to follow.
- **File chips** — images and attachments (`![img](pic.png)`, `[[report.pdf]]`,
  `[file](archive.zip)`) render as a tidy type badge instead of a broken link;
  press the number to open the file in the system default app.
- **Instant paging** — one keypress, no Enter: arrows, `PgUp`/`PgDn`,
  `Home`/`End`, vim keys `j`/`k`/`g`/`G`.
- **Search** — `/` over text, `n`/`N` between matches.
- **Note browser** — arrow-key folder navigation, `Enter` opens.
- **Edit in place** — `e` opens the file in `$EDITOR` (or `nano`/`vi`/`notepad`).
- **Compatibility** — auto-detects Unicode and OSC 8 hyperlinks, ASCII fallback
  for legacy consoles; Linux, macOS, Windows.

---

## Controls

### File view

| Keys                | Action                          |
|---------------------|---------------------------------|
| `↓` `j` `Enter`     | line down                       |
| `↑` `k`             | line up                         |
| `Space` `PgDn` `f`  | page down                       |
| `b` `PgUp`          | page up                         |
| `g` `Home`          | to start                        |
| `G` `End`           | to end                          |
| `1`–`9`             | follow the link with that number|
| `/`                 | search text                     |
| `n` / `N`           | next / previous match           |
| `e`                 | edit file                       |
| `r`                 | reload                          |
| `?` `h`             | help                            |
| `q` `Esc`           | back / quit                     |

### Note browser

| Keys            | Action              |
|-----------------|---------------------|
| `↑` `↓`         | select item         |
| `Enter` `→`     | open file or folder |
| `←` `Backspace` | go up one level     |
| `q` `Esc`       | quit                |

The Russian keyboard layout works on the same keys: `й` = `q`, `у` = `e`, and so on.

---

## Links

Every link in the document is tagged with a number `[1]`, `[2]`, … in reading
order. Pressing the number follows it:

- **Wiki-link** `[[Note]]` opens `Note.md` — first next to the current file,
  then recursively across the opened folder. If the note doesn't exist, you'll
  be offered to create it.
- **Alias** `[[Note|visible text]]` shows the text and follows the file.
- **External link** `[text](https://…)` opens in the browser; in modern
  terminals it's also directly clickable (OSC 8).
- **File / attachment** `[[report.pdf]]`, `[file](data.zip)` — a colored type
  badge (`IMG`, `PDF`, `ARCHIVE`, …); the number opens it in the default app.
  Embedded images `![alt](pic.png)` and `![[pic.png]]` show the badge inline.

---

## Example

````markdown
---
title: Note
tags: demo
---

# Heading

Text with **emphasis** and a link to [[Ideas]].

- [x] done
- [ ] planned

```python
def hello(name):
    return f"Hello, {name}!"
```
````

---

## License

[MIT](LICENSE)
