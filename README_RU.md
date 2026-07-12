<p align="center">
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/English-555c66?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2MCAzMCI%2bPGNsaXBQYXRoIGlkPSJhIj48cGF0aCBkPSJNMCAwdjMwaDYwVjB6Ii8%2bPC9jbGlwUGF0aD48cGF0aCBkPSJNMCAwdjMwaDYwVjB6IiBmaWxsPSIjMDEyMTY5Ii8%2bPHBhdGggZD0iTTAgMGw2MCAzMG0wLTMwTDAgMzAiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSI2Ii8%2bPHBhdGggZD0iTTAgMGw2MCAzMG0wLTMwTDAgMzAiIGNsaXAtcGF0aD0idXJsKCNhKSIgc3Ryb2tlPSIjQzgxMDJFIiBzdHJva2Utd2lkdGg9IjQiLz48cGF0aCBkPSJNMzAgMHYzME0wIDE1aDYwIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMTAiLz48cGF0aCBkPSJNMzAgMHYzME0wIDE1aDYwIiBzdHJva2U9IiNDODEwMkUiIHN0cm9rZS13aWR0aD0iNiIvPjwvc3ZnPgo%3d"></a>
  <a href="README_RU.md"><img alt="Русский" src="https://img.shields.io/badge/%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-0969da?style=for-the-badge&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA5IDYiPjxwYXRoIGZpbGw9IiNmZmYiIGQ9Ik0wIDBoOXYySDB6Ii8%2bPHBhdGggZmlsbD0iIzAwMzlBNiIgZD0iTTAgMmg5djJIMHoiLz48cGF0aCBmaWxsPSIjRDUyQjFFIiBkPSJNMCA0aDl2MkgweiIvPjwvc3ZnPgo%3d"></a>
</p>

<h1 align="center">md</h1>

<p align="center">
  <strong>Читалка Markdown для терминала.</strong>
</p>

<p align="center">
  Один файл · Чистый Python · Ноль зависимостей
</p>

---

```bash
python md.py README.md      # открыть файл
python md.py ~/заметки      # открыть папку заметок
python md.py                # текущая папка
```

Требуется только Python 3.8+. Никаких `pip install`.

---

## Возможности

- **Полный рендер Markdown** — заголовки, списки, чек-боксы, цитаты, таблицы,
  горизонтальные линии, YAML front-matter, перенос строк по ширине терминала.
- **Инлайн-форматирование** — жирный, курсив, зачёркнутый, `код`, выделение `==текст==`.
- **Код с подсветкой** — Python, Bash, JavaScript/TypeScript, JSON и generic-фолбэк;
  блоки в рамке без номеров строк и боковых полос — выделение в терминале
  копирует ровно код, без мусора.
- **Переходы по ссылкам** — вики-ссылки `[[Заметка]]` и `[[Заметка|алиас]]`,
  обычные `[текст](url)`. Каждая ссылка получает номер — нажмите его, чтобы перейти.
- **Чипы файлов** — картинки и вложения (`![img](pic.png)`, `[[отчёт.pdf]]`,
  `[файл](archive.zip)`) отображаются аккуратным бейджем типа, а не поломанной
  ссылкой; по номеру файл открывается в системном приложении.
- **Мгновенное листание** — одна клавиша без Enter: стрелки, `PgUp`/`PgDn`,
  `Home`/`End`, vim-клавиши `j`/`k`/`g`/`G`.
- **Поиск** — `/` по тексту, `n`/`N` между совпадениями.
- **Браузер заметок** — навигация по папкам стрелками, `Enter` открывает.
- **Правка на месте** — `e` открывает файл в `$EDITOR` (либо `nano`/`vi`/`notepad`).
- **Совместимость** — автоопределение Unicode и OSC 8-гиперссылок,
  ASCII-фолбэк для старых консолей; Linux, macOS, Windows.

---

## Управление

### Просмотр файла

| Клавиши             | Действие                            |
|---------------------|-------------------------------------|
| `↓` `j` `Enter`     | строка вниз                         |
| `↑` `k`             | строка вверх                        |
| `Пробел` `PgDn` `f` | страница вниз                       |
| `b` `PgUp`          | страница вверх                      |
| `g` `Home`          | в начало                            |
| `G` `End`           | в конец                             |
| `1`–`9`             | перейти по ссылке с этим номером    |
| `/`                 | поиск по тексту                     |
| `n` / `N`           | следующее / предыдущее совпадение   |
| `e`                 | редактировать файл                  |
| `r`                 | обновить                            |
| `?` `h`             | справка                             |
| `q` `Esc`           | назад / выход                       |

### Браузер заметок

| Клавиши         | Действие               |
|-----------------|------------------------|
| `↑` `↓`         | выбор пункта           |
| `Enter` `→`     | открыть файл или папку |
| `←` `Backspace` | на уровень вверх       |
| `q` `Esc`       | выход                  |

Русская раскладка работает на тех же клавишах: `й` = `q`, `у` = `e` и так далее.

---

## Ссылки

Каждая ссылка в документе помечается номером `[1]`, `[2]`, … в порядке чтения.
Нажатие номера выполняет переход:

- **Вики-ссылка** `[[Заметка]]` открывает файл `Заметка.md` — сначала рядом
  с текущим файлом, затем рекурсивно по всей открытой папке.
  Если заметки не существует, будет предложено создать её.
- **Алиас** `[[Заметка|видимый текст]]` показывает текст, переход идёт по файлу.
- **Внешняя ссылка** `[текст](https://…)` открывается в браузере;
  в современных терминалах она также кликабельна напрямую (OSC 8).
- **Файл / вложение** `[[отчёт.pdf]]`, `[файл](data.zip)` — цветной бейдж типа
  (`IMG`, `PDF`, `ARCHIVE`, …); номер открывает файл в системном приложении.
  Встроенные картинки `![alt](pic.png)` и `![[pic.png]]` показывают бейдж в тексте.

---

## Пример

````markdown
---
title: Заметка
tags: демо
---

# Заголовок

Текст с **акцентом** и ссылкой на [[Идеи]].

- [x] сделано
- [ ] в планах

```python
def hello(name):
    return f"Привет, {name}!"
```
````

---

## Лицензия

[MIT](LICENSE)
