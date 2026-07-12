import os
import sys
import re
import shutil
import subprocess
from pathlib import Path

if os.name == 'nt':
    os.system('color')

IS_TTY = os.environ.get('TERM') == 'linux'
VAULT_ROOT = None

class Style:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    STRIKE = '\033[9m'

    FG_BLACK = '\033[30m'
    FG_RED = '\033[91m'
    FG_GREEN = '\033[92m'
    FG_YELLOW = '\033[93m'
    FG_BLUE = '\033[94m'
    FG_MAGENTA = '\033[95m'
    FG_CYAN = '\033[96m'
    FG_WHITE = '\033[97m'

    BG_BLUE = '\033[44m'
    BG_DARK = '\033[100m'

ICONS = {
    "img": "[IMG]" if IS_TTY else "📷",
    "dir": "[DIR]" if IS_TTY else "📁",
    "file": "[MD]" if IS_TTY else "📝",
    "lock": "[LOCKED]" if IS_TTY else "🔒",
    "up": "<-" if IS_TTY else "⤴",
    "check": "[V]" if IS_TTY else "[✔]",
    "quote": "|" if IS_TTY else "▌",
    "bullet": "*" if IS_TTY else "•",
    "h3": ">" if IS_TTY else "▶",
    "edit": "[EDIT]" if IS_TTY else "✏️"
}

SYNTAX_RULES = {
    'python': [
        ('COMMENT', r'#.*'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('DECORATOR', r'@\w+'),
        ('KEYWORD', r'\b(?:def|class|return|if|elif|else|for|while|in|import|from|as|try|except|finally|pass|lambda|assert|and|or|not|is|with|global|nonlocal|yield|None|True|False)\b'),
        ('NUMBER', r'\b\d+\b'),
        ('FUNCTION', r'\b\w+(?=\s*\()'),
        ('BUILTIN', r'\b(?:print|len|range|str|int|float|list|dict|set|tuple|open|type|enumerate|zip|sum|min|max|abs|any|all)\b'),
    ],
    'bash': [
        ('COMMENT', r'#.*'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('VARIABLE', r'\$\w+|\$\{\w+\}'),
        ('KEYWORD', r'\b(?:if|then|elif|else|fi|case|esac|for|while|until|do|done|in|function|local|return|exit|export)\b'),
        ('NUMBER', r'\b\d+\b'),
    ],
    'sh': [
        ('COMMENT', r'#.*'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('VARIABLE', r'\$\w+|\$\{\w+\}'),
        ('KEYWORD', r'\b(?:if|then|elif|else|fi|case|esac|for|while|until|do|done|in|function|local|return|exit|export)\b'),
        ('NUMBER', r'\b\d+\b'),
    ],
    'json': [
        ('KEY', r'"[^"\\]*"(?=\s*:)'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"'),
        ('NUMBER', r'\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b'),
        ('KEYWORD', r'\b(?:true|false|null)\b'),
    ],
    'generic': [
        ('COMMENT', r'#.*|//.*'),
        ('STRING', r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('KEYWORD', r'\b(?:if|else|for|while|return|function|class|def|import|const|let|var|void|int|char|float|double|bool|true|false)\b'),
        ('NUMBER', r'\b\d+\b'),
    ]
}

TOKEN_COLORS = {
    'COMMENT': Style.DIM + Style.FG_GREEN,
    'STRING': Style.FG_GREEN,
    'DECORATOR': Style.FG_BLUE,
    'KEYWORD': Style.FG_MAGENTA,
    'NUMBER': Style.FG_CYAN,
    'FUNCTION': Style.FG_BLUE,
    'BUILTIN': Style.FG_YELLOW,
    'VARIABLE': Style.FG_CYAN,
    'KEY': Style.FG_BLUE,
}

COMPILED_RULES = {}
for lang, rules in SYNTAX_RULES.items():
    pattern = '|'.join(f'(?P<{name}>{pat})' for name, pat in rules)
    COMPILED_RULES[lang] = re.compile(pattern)

def highlight_code_line(line, lang):
    regex = COMPILED_RULES.get(lang, COMPILED_RULES['generic'])
    def repl(match):
        for name, val in match.groupdict().items():
            if val is not None:
                color = TOKEN_COLORS.get(name, '')
                return f"{color}{val}{Style.RESET}"
        return match.group(0)
    return regex.sub(repl, line)

def find_note_globally(target_name, current_dir):
    p = current_dir / f"{target_name}.md"
    if p.is_file(): return p
    p = current_dir / target_name
    if p.is_file(): return p
    
    global VAULT_ROOT
    if VAULT_ROOT:
        try:
            for p in VAULT_ROOT.rglob("*.md"):
                if p.stem.lower() == target_name.lower():
                    return p
        except Exception:
            pass
            
    return current_dir / f"{target_name}.md"

def parse_wikilinks(text, found_links, current_dir):
    def repl(match):
        target = match.group(1).strip()
        alias = match.group(2).strip() if match.group(2) else target
        
        target_path = find_note_globally(target, current_dir)
        link_index = len(found_links) + 1
        found_links.append((target, target_path))
        
        if IS_TTY:
            return f"{Style.FG_CYAN}{Style.UNDERLINE}[{link_index}] {alias}{Style.RESET}"
        else:
            return f"{Style.FG_MAGENTA}{Style.BOLD}{alias}{Style.RESET} {Style.DIM}⟦{link_index}⟧{Style.RESET}"

    return re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', repl, text)

def make_link_clickable(text, url):
    if IS_TTY:
        return f"{Style.FG_BLUE}{Style.UNDERLINE}{text}{Style.RESET} ({Style.DIM}{url}{Style.RESET})"
    return f"\033]8;;{url}\033\\{Style.FG_BLUE}{Style.BOLD}{text}{Style.RESET} {Style.DIM}⟦↗⟧{Style.RESET}\033]8;;\033\\"

def parse_inline(text, found_links=None, current_dir=None):
    if found_links is not None and current_dir is not None:
        text = parse_wikilinks(text, found_links, current_dir)

    text = re.sub(r'!\[(.*?)\]\((.*?)\)', f'{Style.FG_MAGENTA}{ICONS["img"]} [Изображение: \\1]{Style.RESET}', text)
    text = re.sub(r'\[([^\]]+)\]\((.*?)\)', lambda m: make_link_clickable(m.group(1), m.group(2)), text)
    text = re.sub(r'\*\*(.+?)\*\*|__(.+?)__', f'{Style.BOLD}\\1\\2{Style.RESET}', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', f'{Style.ITALIC}\\1{Style.RESET}', text)
    text = re.sub(r'~~(.+?)~~', f'{Style.STRIKE}\\1{Style.RESET}', text)
    text = re.sub(r'`([^`]+)`', f'{Style.BG_DARK}{Style.FG_YELLOW} \\1 {Style.RESET}', text)
    return text

def render_markdown_to_lines(filepath, found_links, current_dir):
    rendered_lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        return [f"{Style.FG_RED}Ошибка чтения файла: {e}{Style.RESET}"]

    term_width = shutil.get_terminal_size().columns
    in_code_block = False
    current_code_lang = 'generic'

    rendered_lines.append("")

    for line in lines:
        raw = line.rstrip('\n')

        if raw.strip().startswith('```'):
            in_code_block = not in_code_block
            if in_code_block:
                lang = raw.strip()[3:].strip().lower()
                current_code_lang = lang if lang in COMPILED_RULES else 'generic'
                if IS_TTY:
                    rendered_lines.append(f"{Style.DIM}--- Code block ({current_code_lang}) ---{Style.RESET}")
                else:
                    hdr = f" ╭── code: {current_code_lang} "
                    line_len = max(5, term_width - len(hdr) - 1)
                    rendered_lines.append(f"{Style.DIM}{hdr}{'─' * line_len}╮{Style.RESET}")
            else:
                if IS_TTY:
                    rendered_lines.append(f"{Style.DIM}--- End of code ---{Style.RESET}\n")
                else:
                    rendered_lines.append(f"{Style.DIM} ╰{'─' * (term_width - 3)}╯{Style.RESET}\n")
            continue

        if in_code_block:
            rendered_lines.append(highlight_code_line(raw, current_code_lang))
            continue

        if re.match(r'^(\*|-|_){3,}\s*$', raw):
            rendered_lines.append(f"{Style.DIM}{'━' * term_width}{Style.RESET}")
            continue

        h_match = re.match(r'^(#{1,6})\s+(.*)', raw)
        if h_match:
            level = len(h_match.group(1))
            title = parse_inline(h_match.group(2), found_links, current_dir)
            plain_title_len = len(re.sub(r'\033\[.*?m|\033\].*?\033\\', '', title))

            rendered_lines.append("")
            if level == 1:
                pad = max(0, (term_width - plain_title_len) // 2 - 1)
                rendered_lines.append(f"{Style.BG_BLUE}{Style.FG_WHITE}{Style.BOLD}{' ' * pad} {title} {' ' * pad}{Style.RESET}")
                rendered_lines.append("")
            elif level == 2:
                rendered_lines.append(f"{Style.FG_CYAN}{Style.BOLD}{title}{Style.RESET}")
                rendered_lines.append(f"{Style.FG_CYAN}{'━' * term_width}{Style.RESET}")
            elif level == 3:
                rendered_lines.append(f"{Style.FG_GREEN}{Style.BOLD}{ICONS['h3']} {title}{Style.RESET}")
            elif level == 4:
                rendered_lines.append(f"{Style.FG_YELLOW}{Style.UNDERLINE}{title}{Style.RESET}")
            elif level == 5:
                rendered_lines.append(f"{Style.FG_MAGENTA}{Style.BOLD}{title}{Style.RESET}")
            elif level == 6:
                rendered_lines.append(f"{Style.DIM}{Style.ITALIC}{title}{Style.RESET}")
            continue

        if raw.startswith('> '):
            quote_text = parse_inline(raw[2:], found_links, current_dir)
            rendered_lines.append(f"{Style.FG_MAGENTA}{ICONS["quote"]} {Style.ITALIC}{quote_text}{Style.RESET}")
            continue

        list_match = re.match(r'^(\s*)([-+]|\d+\.)\s+(.*)', raw)
        if list_match:
            indent = list_match.group(1)
            bullet = list_match.group(2)
            content = list_match.group(3)

            content = re.sub(r'^\[ \]\s+', f'{Style.DIM}[ ]{Style.RESET} ', content)
            content = re.sub(r'^\[(x|X)\]\s+', f'{Style.FG_GREEN}{ICONS["check"]}{Style.RESET} ', content)
            content = parse_inline(content, found_links, current_dir)

            if not bullet[0].isdigit():
                bullet = f"{Style.FG_CYAN}{ICONS['bullet']}{Style.RESET}"
            else:
                bullet = f"{Style.FG_CYAN}{bullet}{Style.RESET}"

            rendered_lines.append(f"{indent}{bullet} {content}")
            continue

        if raw.strip() == "":
            rendered_lines.append("")
        else:
            rendered_lines.append(parse_inline(raw, found_links, current_dir))

    rendered_lines.append("\n" + f"{Style.DIM}{'━' * term_width}{Style.RESET}" + "\n")
    return rendered_lines

def edit_file(filepath):
    editor = os.environ.get('EDITOR')
    if not editor:
        if os.name == 'nt':
            editor = 'notepad'
        else:
            editor = 'nano' if shutil.which('nano') else 'vi'
    try:
        subprocess.call([editor, str(filepath)])
    except Exception as e:
        print(f"{Style.FG_RED}Не удалось запустить редактор ({editor}): {e}{Style.RESET}")
        input("Нажмите Enter для продолжения...")

def run_pager(filepath, current_dir):
    needs_render = True
    current_line = 0
    rendered_lines = []
    found_links = []

    while True:
        if needs_render:
            found_links.clear()
            rendered_lines = render_markdown_to_lines(filepath, found_links, current_dir)
            needs_render = False

        term_height = shutil.get_terminal_size().lines
        term_width = shutil.get_terminal_size().columns
        
        page_height = max(5, term_height - 6)

        os.system('cls' if os.name == 'nt' else 'clear')

        if IS_TTY:
            print(f"{Style.BG_DARK}{Style.FG_WHITE} Просмотр: {filepath.name} {Style.RESET}")
            print(f"{Style.DIM}{'─' * term_width}{Style.RESET}")
        else:
            header = f"  {ICONS['file']} {filepath.name}  "
            bar_len = max(0, (term_width - len(header)) // 2)
            print(f"{Style.DIM}{'━' * bar_len}{Style.RESET}{Style.BG_DARK}{Style.FG_WHITE}{Style.BOLD}{header}{Style.RESET}{Style.DIM}{'━' * bar_len}{Style.RESET}")

        end_line = min(current_line + page_height, len(rendered_lines))
        for idx in range(current_line, end_line):
            print(rendered_lines[idx])

        remaining_lines = page_height - (end_line - current_line)
        if remaining_lines > 0:
            print("\n" * remaining_lines)

        print(f"{Style.DIM}{'━' * term_width}{Style.RESET}")

        percent = int((end_line / len(rendered_lines)) * 100) if rendered_lines else 100
        prompt_text = (
            f" Стр: {current_line + 1}-{end_line}/{len(rendered_lines)} ({percent}%) │ "
            f"[Space/Enter] Вниз │ [b] Вверх │ [e] Редактировать │ [q] Назад/Выход"
        )
        if found_links:
            prompt_text += f"\n Найдено ссылок: {len(found_links)}. Введите номер [1-{len(found_links)}] для перехода."

        print(f"{Style.BG_DARK}{Style.FG_WHITE}{prompt_text}{Style.RESET}")

        choice = input(f"{Style.FG_CYAN}> {Style.RESET}").strip().lower()

        if choice == 'q' or choice == 'й':
            break
        elif choice == 'e' or choice == 'у':
            edit_file(filepath)
            needs_render = True
            current_line = 0
        elif choice == 'b' or choice == 'и':
            current_line = max(0, current_line - page_height)
        elif choice == '' or choice == ' ':
            if end_line >= len(rendered_lines):
                break
            else:
                current_line = min(len(rendered_lines) - 1, current_line + page_height)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(found_links):
                target_name, target_path = found_links[idx]
                
                if target_path.is_file():
                    run_pager(target_path, current_dir)
                    needs_render = True
                else:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"{Style.FG_YELLOW}Заметка '{target_name}' еще не создана.{Style.RESET}\n")
                    create = input("Создать новую заметку? [y/N]: ").strip().lower()
                    if create == 'y' or create == 'н':
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        target_path.write_text(f"# {target_name}\n\n", encoding='utf-8')
                        edit_file(target_path)
                        run_pager(target_path, current_dir)
                        needs_render = True

def browse_directory(current_path):
    current_path = Path(current_path).resolve()

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        term_width = shutil.get_terminal_size().columns

        header = f" {ICONS['dir']} {current_path.name} "
        if IS_TTY:
            print(f"{Style.BG_DARK}{Style.FG_WHITE}{Style.BOLD}{header.center(term_width)}{Style.RESET}\n")
        else:
            bar_len = max(0, (term_width - len(header)) // 2)
            print(f"{Style.DIM}{'━' * bar_len}{Style.RESET}{Style.BG_DARK}{Style.FG_WHITE}{Style.BOLD}{header}{Style.RESET}{Style.DIM}{'━' * bar_len}{Style.RESET}\n")
        print(f"{Style.DIM}Полный путь: {current_path}{Style.RESET}\n")

        items = []
        try:
            for p in sorted(current_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if p.name.startswith('.'): continue
                if p.is_dir() or p.suffix.lower() == '.md':
                    items.append(p)
        except PermissionError:
            print(f"{Style.FG_RED}{ICONS['lock']} Нет доступа к директории.{Style.RESET}\n")

        print(f"  [0] {Style.FG_YELLOW}{ICONS['up']} На уровень вверх{Style.RESET}")
        for i, item in enumerate(items, 1):
            if item.is_dir():
                print(f"  [{i}] {ICONS['dir']} {Style.BOLD}{item.name}{Style.RESET}")
            else:
                print(f"  [{i}] {ICONS['file']} {item.name}{Style.RESET}")

        print("\n" + f"{Style.DIM}{'━' * term_width}{Style.RESET}")
        choice = input(f"Выберите номер (или {Style.FG_RED}'q'{Style.RESET} для выхода): ").strip()

        if choice.lower() == 'q':
            os.system('cls' if os.name == 'nt' else 'clear')
            break
        if choice == '0':
            current_path = current_path.parent
            continue

        if choice.isdigit() and 1 <= int(choice) <= len(items):
            selected = items[int(choice) - 1]
            if selected.is_dir():
                current_path = selected
            else:
                run_pager(selected, current_path)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    target_path = Path(target)

    if target_path.is_dir():
        VAULT_ROOT = target_path
    else:
        VAULT_ROOT = target_path.parent

    if target_path.is_file() and target_path.suffix.lower() == '.md':
        run_pager(target_path, target_path.parent)
    elif target_path.is_dir():
        browse_directory(target_path)
    else:
        print(f"{Style.FG_RED}Файл или папка не найдены, либо это не .md файл{Style.RESET}")

