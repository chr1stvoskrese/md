import os
import sys
import re
import shutil
import subprocess
import webbrowser
from pathlib import Path

if os.name == 'nt':
    os.system('color')

UTF8 = 'utf' in (sys.stdout.encoding or '').lower()
LINUX_CONSOLE = os.environ.get('TERM') == 'linux'
UNICODE = UTF8 and not LINUX_CONSOLE
OSC8 = UNICODE and os.environ.get('TERM') not in ('dumb', 'linux')

VAULT_ROOT = None


class Style:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    REVERSE = '\033[7m'
    STRIKE = '\033[9m'

    FG_RED = '\033[91m'
    FG_GREEN = '\033[92m'
    FG_YELLOW = '\033[93m'
    FG_BLUE = '\033[94m'
    FG_MAGENTA = '\033[95m'
    FG_CYAN = '\033[96m'
    FG_WHITE = '\033[97m'
    FG_GREY = '\033[90m'

    BG_BLUE = '\033[44m'
    BG_CYAN = '\033[46m'
    BG_DARK = '\033[100m'


def theme(unicode_val, ascii_val):
    return unicode_val if UNICODE else ascii_val


ICONS = {
    'img': theme('🖼', '[IMG]'),
    'dir': theme('📁', '[DIR]'),
    'file': theme('📄', '[MD]'),
    'lock': theme('🔒', '[X]'),
    'up': theme('⬆', '<-'),
    'done': theme('✔', '[x]'),
    'todo': theme('○', '[ ]'),
    'quote': theme('▌', '|'),
    'bullet': theme('•', '*'),
    'sub': theme('◦', '-'),
    'arrow': theme('›', '>'),
    'link': theme('↗', '^'),
    'note': theme('🔗', '=>'),
    'search': theme('🔎', '/'),
}

BOX = {
    'h': theme('─', '-'),
    'v': theme('│', '|'),
    'tl': theme('╭', '+'),
    'tr': theme('╮', '+'),
    'bl': theme('╰', '+'),
    'br': theme('╯', '+'),
    'lt': theme('├', '+'),
    'rt': theme('┤', '+'),
    'tt': theme('┬', '+'),
    'bt': theme('┴', '+'),
    'x': theme('┼', '+'),
    'rule': theme('━', '='),
    'thin': theme('─', '-'),
}

SYNTAX_RULES = {
    'python': [
        ('COMMENT', r'#.*'),
        ('STRING', r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('DECORATOR', r'@\w+'),
        ('KEYWORD', r'\b(?:def|class|return|if|elif|else|for|while|in|import|from|as|try|except|finally|raise|pass|break|continue|lambda|assert|and|or|not|is|with|global|nonlocal|yield|async|await|None|True|False)\b'),
        ('BUILTIN', r'\b(?:print|len|range|str|int|float|list|dict|set|tuple|open|type|enumerate|zip|sum|min|max|abs|any|all|sorted|map|filter|isinstance|super|self)\b'),
        ('NUMBER', r'\b\d+(?:\.\d+)?\b'),
        ('FUNCTION', r'\b\w+(?=\s*\()'),
    ],
    'bash': [
        ('COMMENT', r'#.*'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\']*\''),
        ('VARIABLE', r'\$\w+|\$\{[^}]+\}'),
        ('KEYWORD', r'\b(?:if|then|elif|else|fi|case|esac|for|while|until|do|done|in|function|local|return|exit|export|source|echo|cd|sudo)\b'),
        ('NUMBER', r'\b\d+\b'),
    ],
    'javascript': [
        ('COMMENT', r'//.*|/\*[\s\S]*?\*/'),
        ('STRING', r'`[^`]*`|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('KEYWORD', r'\b(?:const|let|var|function|return|if|else|for|while|class|new|this|import|from|export|default|async|await|try|catch|finally|throw|typeof|instanceof|null|undefined|true|false)\b'),
        ('NUMBER', r'\b\d+(?:\.\d+)?\b'),
        ('FUNCTION', r'\b\w+(?=\s*\()'),
    ],
    'json': [
        ('KEY', r'"[^"\\]*"(?=\s*:)'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"'),
        ('NUMBER', r'-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b'),
        ('KEYWORD', r'\b(?:true|false|null)\b'),
    ],
    'generic': [
        ('COMMENT', r'#.*|//.*'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('KEYWORD', r'\b(?:if|else|for|while|return|function|func|def|class|import|from|const|let|var|void|int|char|float|double|bool|public|private|static|true|false|null|nil|None)\b'),
        ('NUMBER', r'\b\d+(?:\.\d+)?\b'),
    ],
}

SYNTAX_RULES['py'] = SYNTAX_RULES['python']
SYNTAX_RULES['sh'] = SYNTAX_RULES['bash']
SYNTAX_RULES['shell'] = SYNTAX_RULES['bash']
SYNTAX_RULES['zsh'] = SYNTAX_RULES['bash']
SYNTAX_RULES['js'] = SYNTAX_RULES['javascript']
SYNTAX_RULES['ts'] = SYNTAX_RULES['javascript']
SYNTAX_RULES['typescript'] = SYNTAX_RULES['javascript']

TOKEN_COLORS = {
    'COMMENT': Style.DIM + Style.FG_GREEN,
    'STRING': Style.FG_GREEN,
    'DECORATOR': Style.FG_BLUE,
    'KEYWORD': Style.FG_MAGENTA + Style.BOLD,
    'NUMBER': Style.FG_CYAN,
    'FUNCTION': Style.FG_BLUE,
    'BUILTIN': Style.FG_YELLOW,
    'VARIABLE': Style.FG_CYAN,
    'KEY': Style.FG_BLUE,
}

COMPILED_RULES = {}
for _lang, _rules in SYNTAX_RULES.items():
    _pattern = '|'.join(f'(?P<{name}>{pat})' for name, pat in _rules)
    COMPILED_RULES[_lang] = re.compile(_pattern)

ANSI_TOKEN = re.compile(r'\033\[[0-9;]*m|\033\]8;;[^\033]*\033\\')


def strip_ansi(text):
    return ANSI_TOKEN.sub('', text)


def visible_len(text):
    return len(strip_ansi(text))


def tokenize_ansi(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        m = ANSI_TOKEN.match(text, i)
        if m:
            out.append(('e', m.group(0)))
            i = m.end()
        else:
            out.append(('c', text[i]))
            i += 1
    return out


def wrap_ansi(text, width, indent=''):
    text = text.replace('\t', '    ')
    width = max(1, width)
    cells = []
    ctrl = ''
    for kind, val in tokenize_ansi(text):
        if kind == 'e':
            ctrl += val
        else:
            cells.append((val, ctrl))
            ctrl = ''
    if ctrl:
        cells.append(('', ctrl))

    lines = []
    sgr = ''
    link = ''
    first = True
    line = ''
    line_w = 0

    def apply(control):
        nonlocal sgr, link
        for m in ANSI_TOKEN.finditer(control):
            tok = m.group(0)
            if tok.startswith('\033]8'):
                link = tok[5:-2]
            elif tok == Style.RESET:
                sgr = ''
                link = ''
            else:
                sgr += tok

    def prefix():
        return sgr + (f'\033]8;;{link}\033\\' if link else '')

    def suffix():
        close = '\033]8;;\033\\' if link else ''
        return close + (Style.RESET if (sgr or link) else '')

    def emit():
        nonlocal line, line_w, first
        pre = '' if first else indent + prefix()
        lines.append(pre + line + suffix())
        line = ''
        line_w = 0
        first = False

    i = 0
    n = len(cells)
    while i < n:
        ch, cc = cells[i]
        if ch == ' ':
            apply(cc)
            if 0 < line_w < width:
                line += cc + ' '
                line_w += 1
            else:
                line += cc
            i += 1
            continue
        j = i
        word_w = 0
        while j < n and cells[j][0] != ' ':
            if cells[j][0] != '':
                word_w += 1
            j += 1
        if line_w > 0 and line_w + word_w > width:
            emit()
        if word_w > width and line_w == 0:
            for k in range(i, j):
                cch, ccc = cells[k]
                apply(ccc)
                if cch == '':
                    line += ccc
                    continue
                if line_w >= width:
                    emit()
                line += ccc + cch
                line_w += 1
            i = j
            continue
        for k in range(i, j):
            cch, ccc = cells[k]
            apply(ccc)
            line += ccc + cch
            if cch != '':
                line_w += 1
        i = j
    emit()
    return lines


def highlight_code_line(line, lang):
    regex = COMPILED_RULES.get(lang, COMPILED_RULES['generic'])

    def repl(match):
        name = match.lastgroup
        val = match.group()
        color = TOKEN_COLORS.get(name, '')
        return f'{color}{val}{Style.RESET}'

    return regex.sub(repl, line)


def find_note_globally(target_name, current_dir):
    direct = current_dir / f'{target_name}.md'
    if direct.is_file():
        return direct
    direct = current_dir / target_name
    if direct.is_file():
        return direct
    if VAULT_ROOT:
        try:
            for p in VAULT_ROOT.rglob('*.md'):
                if p.stem.lower() == target_name.lower():
                    return p
        except Exception:
            pass
    return current_dir / f'{target_name}.md'


def add_note_link(found_links, target, current_dir):
    path = find_note_globally(target, current_dir)
    found_links.append(('note', target, path))
    return len(found_links)


def add_url_link(found_links, url):
    found_links.append(('url', url, url))
    return len(found_links)


def badge(index, color):
    return f'{color}{Style.BOLD}[{index}]{Style.RESET}'


def render_note_link(alias, index):
    return (f'{Style.FG_CYAN}{Style.UNDERLINE}{alias}{Style.RESET}'
            f'{badge(index, Style.FG_CYAN)}')


def render_url_link(text, url, index):
    label = f'{Style.FG_BLUE}{Style.UNDERLINE}{text}{Style.RESET}'
    if OSC8:
        label = f'\033]8;;{url}\033\\{label}\033]8;;\033\\'
    return f'{label}{badge(index, Style.FG_BLUE)}'


LINK_RE = re.compile(
    r'!\[(?P<img>[^\]]*)\]\((?P<imgurl>[^)]*)\)'
    r'|\[\[(?P<wl>[^\]|#]+)(?:#[^\]|]+)?(?:\|(?P<alias>[^\]]+))?\]\]'
    r'|\[(?P<txt>[^\]]+)\]\((?P<url>[^)]*)\)'
)


def parse_links(text, found_links, current_dir):
    def repl(m):
        if m.group('img') is not None:
            alt = m.group('img') or 'изображение'
            return f'{Style.FG_MAGENTA}{ICONS["img"]} {alt}{Style.RESET}'
        if m.group('wl') is not None:
            target = m.group('wl').strip()
            alias = (m.group('alias') or target).strip()
            idx = add_note_link(found_links, target, current_dir)
            return render_note_link(alias, idx)
        text_part = m.group('txt')
        url = m.group('url') or ''
        idx = add_url_link(found_links, url)
        return render_url_link(text_part, url, idx)

    return LINK_RE.sub(repl, text)


def parse_inline(text, found_links=None, current_dir=None):
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f'\x00{len(codes) - 1}\x00'

    text = re.sub(r'`([^`]+)`', stash, text)

    if found_links is not None and current_dir is not None:
        text = parse_links(text, found_links, current_dir)

    text = re.sub(r'\*\*(.+?)\*\*|__(.+?)__', lambda m: f'{Style.BOLD}{m.group(1) or m.group(2)}{Style.RESET}', text)
    text = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)\*(?!\*)', f'{Style.ITALIC}\\1{Style.RESET}', text)
    text = re.sub(r'(?<!_)_(?!_)([^_]+?)_(?!_)', f'{Style.ITALIC}\\1{Style.RESET}', text)
    text = re.sub(r'~~(.+?)~~', f'{Style.STRIKE}\\1{Style.RESET}', text)
    text = re.sub(r'==(.+?)==', f'{Style.REVERSE}\\1{Style.RESET}', text)

    def restore(m):
        return f'{Style.BG_DARK}{Style.FG_YELLOW} {codes[int(m.group(1))]} {Style.RESET}'

    text = re.sub(r'\x00(\d+)\x00', restore, text)
    return text


def render_table(rows, width, out):
    grid = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip('|').split('|')]
        grid.append(cells)
    cols = max(len(r) for r in grid)
    grid = [r + [''] * (cols - len(r)) for r in grid]
    widths = [0] * cols
    for r in grid:
        for c in range(cols):
            widths[c] = max(widths[c], visible_len(parse_inline(r[c])))
    total = sum(widths) + 3 * cols + 1
    if total > width:
        avail = max(cols, width - 3 * cols - 1)
        base = max(3, avail // cols)
        widths = [min(w, base) for w in widths]

    def hline(left, mid, right):
        parts = [BOX['h'] * (w + 2) for w in widths]
        return f'{Style.FG_GREY}{left}{mid.join(parts)}{right}{Style.RESET}'

    def render_row(cells, header=False):
        pieces = []
        for c in range(cols):
            content = parse_inline(cells[c])
            if header:
                content = f'{Style.BOLD}{Style.FG_CYAN}{content}{Style.RESET}'
            vis = visible_len(content)
            if vis > widths[c]:
                plain = strip_ansi(content)[:widths[c] - 1] + '…'
                content = plain
                vis = visible_len(content)
            pad = ' ' * (widths[c] - vis)
            pieces.append(f' {content}{pad} ')
        sep = f'{Style.FG_GREY}{BOX["v"]}{Style.RESET}'
        return sep + sep.join(pieces) + sep

    out.append(hline(BOX['tl'], BOX['tt'], BOX['tr']))
    out.append(render_row(grid[0], header=True))
    out.append(hline(BOX['lt'], BOX['x'], BOX['rt']))
    for r in grid[2:]:
        out.append(render_row(r))
    out.append(hline(BOX['bl'], BOX['bt'], BOX['br']))


def render_markdown_to_lines(filepath, found_links, current_dir):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            src = f.read().split('\n')
    except Exception as e:
        return [f'{Style.FG_RED}Ошибка чтения файла: {e}{Style.RESET}']

    width = max(20, shutil.get_terminal_size().columns)
    body = max(20, width - 2)
    out = ['']

    def add(text, indent=''):
        for piece in wrap_ansi(text, body, indent):
            out.append('  ' + piece)

    def raw(text):
        out.append(text)

    i = 0
    n = len(src)

    if n and src[0].strip() == '---':
        j = 1
        meta = []
        while j < n and src[j].strip() != '---':
            meta.append(src[j])
            j += 1
        if j < n:
            raw(f'  {Style.FG_GREY}{BOX["tl"]}{BOX["h"] * (body - 1)}{Style.RESET}')
            for m in meta:
                if ':' in m:
                    key, _, val = m.partition(':')
                    line = f'{Style.FG_GREY}{BOX["v"]} {Style.FG_CYAN}{key.strip()}{Style.FG_GREY}: {Style.RESET}{val.strip()}'
                else:
                    line = f'{Style.FG_GREY}{BOX["v"]} {m}{Style.RESET}'
                for piece in wrap_ansi(line, body, f'{Style.FG_GREY}{BOX["v"]}   '):
                    out.append('  ' + piece)
            raw(f'  {Style.FG_GREY}{BOX["bl"]}{BOX["h"] * (body - 1)}{Style.RESET}')
            out.append('')
            i = j + 1

    code_lang = 'generic'
    while i < n:
        line = src[i]
        stripped = line.strip()

        if stripped.startswith('```') or stripped.startswith('~~~'):
            fence = stripped[:3]
            lang = stripped[3:].strip().lower()
            code_lang = lang if lang in COMPILED_RULES else 'generic'
            label = f' {ICONS["arrow"]} {lang or "код"} '
            fill = max(0, body - visible_len(label) - 2)
            raw(f'  {Style.FG_GREY}{BOX["tl"]}{label}{BOX["h"] * fill}{BOX["tr"]}{Style.RESET}')
            i += 1
            ln = 1
            while i < n and not src[i].strip().startswith(fence):
                gutter = f'{Style.FG_GREY}{BOX["v"]} {Style.DIM}{ln:>3}{Style.RESET} {Style.FG_GREY}{BOX["v"]}{Style.RESET} '
                cont = f'{Style.FG_GREY}{BOX["v"]}     {BOX["v"]}{Style.RESET} '
                content = highlight_code_line(src[i].replace('\t', '    '), code_lang)
                pieces = wrap_ansi(content, body - 8, '')
                if not pieces:
                    pieces = ['']
                out.append('  ' + gutter + pieces[0])
                for extra in pieces[1:]:
                    out.append('  ' + cont + extra)
                ln += 1
                i += 1
            raw(f'  {Style.FG_GREY}{BOX["bl"]}{BOX["h"] * (body - 1)}{Style.RESET}')
            i += 1
            continue

        if re.match(r'^\s*(\*|-|_)( *\1){2,}\s*$', line):
            raw(f'  {Style.FG_GREY}{BOX["rule"] * body}{Style.RESET}')
            i += 1
            continue

        if (re.match(r'^\s*\|.*\|\s*$', line) and i + 1 < n
                and re.match(r'^\s*\|?[\s:|-]+\|?\s*$', src[i + 1]) and '-' in src[i + 1]):
            rows = []
            while i < n and re.match(r'^\s*\|.*\|\s*$', src[i]):
                rows.append(src[i])
                i += 1
            table_out = []
            render_table(rows, body, table_out)
            for t in table_out:
                out.append('  ' + t)
            continue

        h = re.match(r'^(#{1,6})\s+(.*)', line)
        if h:
            level = len(h.group(1))
            title = parse_inline(h.group(2).rstrip(' #'), found_links, current_dir)
            out.append('')
            if level == 1:
                plain = visible_len(title)
                pad = max(1, (body - plain - 2) // 2)
                bar = BOX['rule']
                tail = max(0, body - plain - pad - 2)
                raw(f'  {Style.FG_BLUE}{bar * body}{Style.RESET}')
                raw(f'  {Style.BG_BLUE}{Style.FG_WHITE}{Style.BOLD}{" " * pad} {title} {" " * tail}{Style.RESET}')
                raw(f'  {Style.FG_BLUE}{bar * body}{Style.RESET}')
            elif level == 2:
                add(f'{Style.FG_CYAN}{Style.BOLD}{title}{Style.RESET}')
                raw(f'  {Style.FG_CYAN}{BOX["rule"] * body}{Style.RESET}')
            elif level == 3:
                add(f'{Style.FG_GREEN}{Style.BOLD}{ICONS["arrow"]} {title}{Style.RESET}', '    ')
            elif level == 4:
                add(f'{Style.FG_YELLOW}{Style.BOLD}{Style.UNDERLINE}{title}{Style.RESET}')
            elif level == 5:
                add(f'{Style.FG_MAGENTA}{Style.BOLD}{title}{Style.RESET}')
            else:
                add(f'{Style.DIM}{Style.ITALIC}{title}{Style.RESET}')
            out.append('')
            i += 1
            continue

        q = re.match(r'^\s*>\s?(.*)', line)
        if q:
            block = []
            while i < n and re.match(r'^\s*>', src[i]):
                block.append(re.sub(r'^\s*>\s?', '', src[i]))
                i += 1
            for b in block:
                text = parse_inline(b, found_links, current_dir)
                prefix = f'{Style.FG_MAGENTA}{ICONS["quote"]}{Style.RESET} {Style.ITALIC}{Style.DIM}'
                add(f'{prefix}{text}{Style.RESET}', f'{Style.FG_MAGENTA}{ICONS["quote"]}{Style.RESET} ')
            continue

        lst = re.match(r'^(\s*)([-+*]|\d+[.)])\s+(.*)', line)
        if lst:
            indent = lst.group(1)
            marker = lst.group(2)
            content = lst.group(3)
            depth = len(indent)

            task = re.match(r'^\[( |x|X)\]\s+(.*)', content)
            if task:
                done = task.group(1).lower() == 'x'
                box = (f'{Style.FG_GREEN}{ICONS["done"]}{Style.RESET}' if done
                       else f'{Style.FG_GREY}{ICONS["todo"]}{Style.RESET}')
                body_text = parse_inline(task.group(2), found_links, current_dir)
                if done:
                    body_text = f'{Style.DIM}{body_text}{Style.RESET}'
                add(f'{indent}{box} {body_text}', f'{indent}  ')
                i += 1
                continue

            content = parse_inline(content, found_links, current_dir)
            if marker[0].isdigit():
                bullet = f'{Style.FG_CYAN}{Style.BOLD}{marker}{Style.RESET}'
            else:
                glyph = ICONS['sub'] if depth >= 2 else ICONS['bullet']
                bullet = f'{Style.FG_CYAN}{glyph}{Style.RESET}'
            pad = ' ' * (len(marker) + 1)
            add(f'{indent}{bullet} {content}', f'{indent}{pad}')
            i += 1
            continue

        if stripped == '':
            out.append('')
            i += 1
            continue

        add(parse_inline(line, found_links, current_dir))
        i += 1

    out.append('')
    raw(f'  {Style.DIM}{BOX["thin"] * body}{Style.RESET}')
    return out


def read_key():
    if not sys.stdin.isatty():
        line = sys.stdin.readline()
        if not line:
            raise KeyboardInterrupt
        token = line.strip()
        if token == '':
            return 'ENTER'
        return token[0]
    if os.name == 'nt':
        import msvcrt
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):
            code = msvcrt.getwch()
            return {'H': 'UP', 'P': 'DOWN', 'K': 'LEFT', 'M': 'RIGHT',
                    'I': 'PGUP', 'Q': 'PGDN', 'G': 'HOME', 'O': 'END'}.get(code, '')
        if ch in ('\r', '\n'):
            return 'ENTER'
        if ch == '\x1b':
            return 'ESC'
        if ch in ('\x08', '\x7f'):
            return 'BACKSPACE'
        return ch
    import termios
    import tty
    import select
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        data = os.read(fd, 1)
        if not data:
            raise KeyboardInterrupt
        b = data[0]
        if b == 0x03:
            raise KeyboardInterrupt
        if b in (0x0d, 0x0a):
            return 'ENTER'
        if b in (0x7f, 0x08):
            return 'BACKSPACE'
        if b == 0x1b:
            if not select.select([fd], [], [], 0.05)[0]:
                return 'ESC'
            nxt = os.read(fd, 1)
            if nxt not in (b'[', b'O'):
                return 'ESC'
            seq = b''
            while select.select([fd], [], [], 0.05)[0]:
                c = os.read(fd, 1)
                if not c:
                    break
                seq += c
                if 0x40 <= c[0] <= 0x7e:
                    break
            if seq.endswith(b'~'):
                num = seq[:-1].split(b';')[0]
                return {b'1': 'HOME', b'3': 'DELETE', b'4': 'END', b'5': 'PGUP',
                        b'6': 'PGDN', b'7': 'HOME', b'8': 'END'}.get(num, '')
            final = seq[-1:] if seq else b''
            return {b'A': 'UP', b'B': 'DOWN', b'C': 'RIGHT', b'D': 'LEFT',
                    b'H': 'HOME', b'F': 'END'}.get(final, '')
        extra = 0
        if b >= 0xf0:
            extra = 3
        elif b >= 0xe0:
            extra = 2
        elif b >= 0xc0:
            extra = 1
        while extra > 0 and select.select([fd], [], [], 0.05)[0]:
            more = os.read(fd, 1)
            if not more:
                break
            data += more
            extra -= 1
        return data.decode('utf-8', 'ignore')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def prompt_line(label, numeric=False, initial=''):
    buf = initial
    while True:
        shown = buf if not numeric else buf
        sys.stdout.write(f'\r\033[2K{Style.BG_DARK}{Style.FG_WHITE} {label} {Style.RESET} {shown}{Style.REVERSE} {Style.RESET}')
        sys.stdout.flush()
        key = read_key()
        if key == 'ENTER':
            sys.stdout.write('\r\033[2K')
            sys.stdout.flush()
            return buf
        if key == 'ESC':
            sys.stdout.write('\r\033[2K')
            sys.stdout.flush()
            return None
        if key == 'BACKSPACE':
            buf = buf[:-1]
            continue
        if isinstance(key, str) and len(key) == 1 and key >= ' ':
            if numeric and not key.isdigit():
                continue
            buf += key


def edit_file(filepath):
    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
    if not editor:
        if os.name == 'nt':
            editor = 'notepad'
        else:
            editor = 'nano' if shutil.which('nano') else 'vi'
    try:
        subprocess.call([editor, str(filepath)])
    except Exception as e:
        print(f'{Style.FG_RED}Не удалось запустить редактор ({editor}): {e}{Style.RESET}')
        input('Нажмите Enter для продолжения...')


def clear_screen():
    sys.stdout.write('\033[H\033[2J' if UNICODE else '')
    if not UNICODE:
        os.system('cls' if os.name == 'nt' else 'clear')
    else:
        os.system('cls' if os.name == 'nt' else 'clear')


HELP_LINES = [
    '',
    f'  {Style.BOLD}{Style.FG_CYAN}Управление просмотром{Style.RESET}',
    '',
    f'  {Style.FG_YELLOW}↓ / j / Enter{Style.RESET}      строка вниз',
    f'  {Style.FG_YELLOW}↑ / k{Style.RESET}              строка вверх',
    f'  {Style.FG_YELLOW}Пробел / PgDn / f{Style.RESET}  страница вниз',
    f'  {Style.FG_YELLOW}b / PgUp{Style.RESET}           страница вверх',
    f'  {Style.FG_YELLOW}g / Home{Style.RESET}           в начало',
    f'  {Style.FG_YELLOW}G / End{Style.RESET}            в конец',
    '',
    f'  {Style.BOLD}{Style.FG_CYAN}Ссылки и поиск{Style.RESET}',
    '',
    f'  {Style.FG_YELLOW}0-9{Style.RESET}                перейти по ссылке с этим номером',
    f'  {Style.FG_YELLOW}/{Style.RESET}                  поиск по тексту',
    f'  {Style.FG_YELLOW}n / N{Style.RESET}              следующее / предыдущее совпадение',
    '',
    f'  {Style.BOLD}{Style.FG_CYAN}Прочее{Style.RESET}',
    '',
    f'  {Style.FG_YELLOW}e{Style.RESET}                  редактировать файл',
    f'  {Style.FG_YELLOW}r{Style.RESET}                  обновить',
    f'  {Style.FG_YELLOW}? / h{Style.RESET}              эта справка',
    f'  {Style.FG_YELLOW}q / Esc{Style.RESET}            назад / выход',
    '',
    f'  {Style.DIM}Нажмите любую клавишу, чтобы вернуться…{Style.RESET}',
]


def show_help():
    clear_screen()
    for line in HELP_LINES:
        print(line)
    read_key()


def run_pager(filepath, current_dir):
    top = 0
    rendered = []
    found_links = []
    last_width = -1
    matches = []
    match_pos = -1
    status = ''

    while True:
        term = shutil.get_terminal_size()
        width = term.columns
        height = term.lines
        page = max(3, height - 4)

        if width != last_width:
            found_links.clear()
            rendered = render_markdown_to_lines(filepath, found_links, current_dir)
            last_width = width

        total = len(rendered)
        max_top = max(0, total - page)
        top = min(top, max_top)

        clear_screen()

        title = f' {ICONS["file"]} {filepath.name} '
        pos_pct = int(((top + page) / total) * 100) if total else 100
        pos_pct = min(100, pos_pct)
        right = f' {pos_pct}% '
        fill = max(0, width - visible_len(title) - visible_len(right))
        print(f'{Style.BG_DARK}{Style.FG_WHITE}{Style.BOLD}{title}{Style.RESET}'
              f'{Style.BG_DARK}{" " * fill}{Style.RESET}'
              f'{Style.BG_DARK}{Style.FG_CYAN}{right}{Style.RESET}')

        end = min(top + page, total)
        for idx in range(top, end):
            print(rendered[idx])
        for _ in range(page - (end - top)):
            print('')

        print(f'{Style.FG_GREY}{BOX["thin"] * width}{Style.RESET}')

        if status:
            hint = f' {status}'
        elif found_links:
            hint = (f' {Style.FG_CYAN}↑↓{Style.RESET} листать   '
                    f'{Style.FG_CYAN}0-9{Style.RESET} ссылка ({len(found_links)})   '
                    f'{Style.FG_CYAN}/{Style.RESET} поиск   '
                    f'{Style.FG_CYAN}e{Style.RESET} правка   '
                    f'{Style.FG_CYAN}?{Style.RESET} помощь   '
                    f'{Style.FG_CYAN}q{Style.RESET} выход')
        else:
            hint = (f' {Style.FG_CYAN}↑↓ / Пробел{Style.RESET} листать   '
                    f'{Style.FG_CYAN}/{Style.RESET} поиск   '
                    f'{Style.FG_CYAN}e{Style.RESET} правка   '
                    f'{Style.FG_CYAN}?{Style.RESET} помощь   '
                    f'{Style.FG_CYAN}q{Style.RESET} выход')
        pad = max(0, width - visible_len(hint))
        print(f'{Style.BG_DARK}{Style.FG_WHITE}{hint}{" " * pad}{Style.RESET}', end='')
        sys.stdout.flush()
        status = ''

        try:
            key = read_key()
        except KeyboardInterrupt:
            break

        if key in ('q', 'ESC', 'й'):
            break
        elif key in ('DOWN', 'j', 'ENTER', 'о'):
            top = min(max_top, top + 1)
        elif key in ('UP', 'k', 'л'):
            top = max(0, top - 1)
        elif key in (' ', 'PGDN', 'f', 'а'):
            if top >= max_top:
                pass
            top = min(max_top, top + page)
        elif key in ('b', 'PGUP', 'и'):
            top = max(0, top - page)
        elif key in ('g', 'HOME', 'п'):
            top = 0
        elif key in ('G', 'END', 'П'):
            top = max_top
        elif key in ('e', 'у'):
            edit_file(filepath)
            last_width = -1
            top = 0
        elif key in ('r', 'к'):
            last_width = -1
        elif key in ('?', 'h', 'р'):
            show_help()
        elif key == '/':
            query = prompt_line(f'{ICONS["search"]} Поиск:')
            if query:
                low = query.lower()
                matches = [i for i, ln in enumerate(rendered) if low in strip_ansi(ln).lower()]
                if matches:
                    match_pos = 0
                    for pi, li in enumerate(matches):
                        if li >= top:
                            match_pos = pi
                            break
                    top = min(max_top, matches[match_pos])
                    status = f'{Style.FG_GREEN}Совпадение {match_pos + 1}/{len(matches)}{Style.RESET} — n/N для перехода'
                else:
                    status = f'{Style.FG_RED}Ничего не найдено: {query}{Style.RESET}'
        elif key in ('n', 'т'):
            if matches:
                match_pos = (match_pos + 1) % len(matches)
                top = min(max_top, matches[match_pos])
                status = f'{Style.FG_GREEN}Совпадение {match_pos + 1}/{len(matches)}{Style.RESET}'
        elif key in ('N', 'Т'):
            if matches:
                match_pos = (match_pos - 1) % len(matches)
                top = min(max_top, matches[match_pos])
                status = f'{Style.FG_GREEN}Совпадение {match_pos + 1}/{len(matches)}{Style.RESET}'
        elif isinstance(key, str) and key.isdigit():
            number = key
            if len(found_links) >= 10:
                rest = prompt_line('Номер ссылки:', numeric=True, initial=key)
                number = rest if rest else key
            if number and number.isdigit():
                idx = int(number) - 1
                if 0 <= idx < len(found_links):
                    follow_link(found_links[idx], current_dir)
                    last_width = -1
                else:
                    status = f'{Style.FG_RED}Нет ссылки с номером {number}{Style.RESET}'


def follow_link(link, current_dir):
    kind, label, target = link
    if kind == 'url':
        clear_screen()
        try:
            webbrowser.open(target)
            print(f'{Style.FG_GREEN}Открываю в браузере:{Style.RESET} {target}')
        except Exception:
            print(f'{Style.FG_YELLOW}Ссылка:{Style.RESET} {target}')
        print(f'\n{Style.DIM}Нажмите любую клавишу…{Style.RESET}')
        read_key()
        return
    if target.is_file():
        run_pager(target, target.parent)
        return
    clear_screen()
    print(f'{Style.FG_YELLOW}Заметка «{label}» ещё не создана.{Style.RESET}\n')
    print(f'Создать её? {Style.FG_GREEN}[y]{Style.RESET} да   {Style.FG_RED}[любая]{Style.RESET} нет')
    if read_key() in ('y', 'Y', 'н', 'Н'):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f'# {label}\n\n', encoding='utf-8')
        edit_file(target)
        run_pager(target, target.parent)


def browse_directory(start_path):
    current = Path(start_path).resolve()
    cursor = 0

    while True:
        clear_screen()
        term = shutil.get_terminal_size()
        width = term.columns

        header = f' {ICONS["dir"]} {current.name or current} '
        fill = max(0, width - visible_len(header))
        print(f'{Style.BG_DARK}{Style.FG_WHITE}{Style.BOLD}{header}{" " * fill}{Style.RESET}')
        print(f'{Style.DIM}{current}{Style.RESET}')
        print(f'{Style.FG_GREY}{BOX["thin"] * width}{Style.RESET}')

        items = []
        try:
            for p in sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if p.name.startswith('.'):
                    continue
                if p.is_dir() or p.suffix.lower() == '.md':
                    items.append(p)
        except PermissionError:
            print(f'{Style.FG_RED}{ICONS["lock"]} Нет доступа к директории.{Style.RESET}')

        entries = [('up', None)] + [('item', p) for p in items]
        cursor = max(0, min(cursor, len(entries) - 1))

        view = max(3, term.lines - 6)
        offset = max(0, cursor - view + 1)
        for vi in range(offset, min(offset + view, len(entries))):
            kind, item = entries[vi]
            selected = vi == cursor
            pointer = f'{Style.FG_CYAN}{ICONS["arrow"]}{Style.RESET} ' if selected else '  '
            if kind == 'up':
                text = f'{Style.FG_YELLOW}{ICONS["up"]} на уровень вверх{Style.RESET}'
            elif item.is_dir():
                text = f'{ICONS["dir"]} {Style.BOLD}{item.name}/{Style.RESET}'
            else:
                text = f'{ICONS["file"]} {item.name}'
            if selected:
                line = f'{pointer}{Style.REVERSE}{Style.BOLD} {strip_ansi(text)} {Style.RESET}'
            else:
                line = f'{pointer}{text}'
            print(line)

        for _ in range(view - (min(offset + view, len(entries)) - offset)):
            print('')

        print(f'{Style.FG_GREY}{BOX["thin"] * width}{Style.RESET}')
        hint = (f' {Style.FG_CYAN}↑↓{Style.RESET} выбор   '
                f'{Style.FG_CYAN}Enter{Style.RESET} открыть   '
                f'{Style.FG_CYAN}← / Backspace{Style.RESET} назад   '
                f'{Style.FG_CYAN}q{Style.RESET} выход')
        pad = max(0, width - visible_len(hint))
        print(f'{Style.BG_DARK}{Style.FG_WHITE}{hint}{" " * pad}{Style.RESET}', end='')
        sys.stdout.flush()

        try:
            key = read_key()
        except KeyboardInterrupt:
            break

        if key in ('q', 'ESC', 'й'):
            clear_screen()
            break
        elif key in ('DOWN', 'j', 'о'):
            cursor = min(len(entries) - 1, cursor + 1)
        elif key in ('UP', 'k', 'л'):
            cursor = max(0, cursor - 1)
        elif key in ('PGDN',):
            cursor = min(len(entries) - 1, cursor + view)
        elif key in ('PGUP',):
            cursor = max(0, cursor - view)
        elif key in ('HOME', 'g'):
            cursor = 0
        elif key in ('END', 'G'):
            cursor = len(entries) - 1
        elif key in ('LEFT', 'BACKSPACE', 'h'):
            current = current.parent
            cursor = 0
        elif key in ('ENTER', 'RIGHT', ' ', 'l'):
            kind, item = entries[cursor]
            if kind == 'up':
                current = current.parent
                cursor = 0
            elif item.is_dir():
                current = item
                cursor = 0
            else:
                run_pager(item, current)


def print_usage():
    name = Path(sys.argv[0]).name
    print(f'{Style.BOLD}{Style.FG_CYAN}md{Style.RESET} — просмотр Markdown в терминале\n')
    print(f'  {Style.FG_YELLOW}python {name} <файл.md>{Style.RESET}     открыть файл')
    print(f'  {Style.FG_YELLOW}python {name} <папка>{Style.RESET}       открыть браузер заметок')
    print(f'  {Style.FG_YELLOW}python {name}{Style.RESET}               текущая папка')


def main():
    global VAULT_ROOT
    target = sys.argv[1] if len(sys.argv) > 1 else '.'

    if target in ('-h', '--help'):
        print_usage()
        return

    target_path = Path(target)
    VAULT_ROOT = target_path if target_path.is_dir() else target_path.parent

    try:
        if target_path.is_file() and target_path.suffix.lower() == '.md':
            run_pager(target_path, target_path.parent)
        elif target_path.is_dir():
            browse_directory(target_path)
        else:
            print(f'{Style.FG_RED}Не найдено или не .md файл:{Style.RESET} {target}\n')
            print_usage()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(Style.RESET)


if __name__ == '__main__':
    main()
