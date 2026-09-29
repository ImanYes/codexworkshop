"""Бот-проверка прототипа «Мехмат» без Ren'Py.

Это не Ren'Py, а маленький симулятор той части языка, что есть в прототипе
(label, menu, if/while, call/jump/return, $ и python-блоки, экраны из ui/hud.rpy).
Бот много раз проживает 4 недели разными стилями и ловит:
- ошибки в коде (NameError, KeyError и т. п.);
- ошибки подстановки [переменная] и текст-тегов, включая {g=женская}мужская{/g};
- несуществующие картинки;
- ошибки в экранах и переполненные сетки grid / vpgrid;
- переменные, которые не сохранятся (сохранение Ren'Py делается через pickle — проверяем на каждом шаге).

Запуск (из папки game/mehmat):
    python3 tools/bot_check.py
Настройки через переменные окружения:
    RUNS=200 WEEKS=4 FEMALE=1 (только героиня) VERBOSE=1
    STYLE=sensible            стили через запятую: random, diligent, skipper, social, sensible
    ACT=о,г,о                 порядок недель как в акте: о — обычная, г — неделя Грузина
    METRICS=out.jsonl         снимок каждого дня (статы, деньги, отношения, ивенты…) для разбора баланса
    OVERRIDE=ZERO_MORALE_LEAVE=10   подменить define/переменную для эксперимента
Настоящую проверку Ren'Py (`renpy . lint`) это не заменяет — только дополняет.
"""
import os, re, sys, types, pickle, random, string, textwrap, traceback, collections

GAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")
SKIP_FILES = {"gui.rpy", "options.rpy", "screens.rpy"}


class SimError(Exception):
    pass


# ---------------------------------------------------------------- parsing

class Node:
    def __init__(self, indent, text, line, file, raw=""):
        self.indent, self.text, self.line, self.file, self.raw = indent, text, line, file, raw
        self.children = []

    def raw_block(self):
        """Исходный текст дочерних строк (для python-блоков)."""
        lines = []
        def walk(n):
            for c in n.children:
                lines.append(c.raw)
                walk(c)
        walk(self)
        return textwrap.dedent("\n".join(lines))


def read_logical_lines(path):
    out = []
    with open(path, encoding="utf8") as f:
        raw = f.read().split("\n")
    i = 0
    while i < len(raw):
        line = raw[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        text = stripped
        start = i
        # склейка строк с незакрытыми скобками
        while depth(text) > 0 and i + 1 < len(raw):
            i += 1
            text += "\n" + raw[i].strip()
        out.append((indent, text, start + 1, "\n".join(raw[start:i + 1])))
        i += 1
    return out


def depth(s):
    d = 0
    q = None
    esc = False
    comment = False
    for ch in s:
        if comment:
            if ch == "\n":
                comment = False
            continue
        if q:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch == "#":
            comment = True
        elif ch in "([{":
            d += 1
        elif ch in ")]}":
            d -= 1
    return d


def parse_file(path, rel):
    root = Node(-1, "<root>", 0, rel)
    stack = [root]
    for indent, text, line, rawtext in read_logical_lines(path):
        while stack[-1].indent >= indent:
            stack.pop()
        n = Node(indent, text, line, rel, rawtext)
        stack[-1].children.append(n)
        stack.append(n)
    return root


# ---------------------------------------------------------------- store & stubs

store = types.ModuleType("store")
sys.modules["store"] = store
S = store.__dict__

TEXT_TEXT, TEXT_TAG = 1, 2


class Character(object):
    def __init__(self, name=None, **kw):
        self.name = name


class Disp(object):
    def __init__(self, *a, **k):
        pass


class Persistent(object):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class Action(object):
    def __init__(self, *a, **k):
        self.a = a


class Rng(random.Random):
    pass


class RenpyStub(types.ModuleType):
    TEXT_TEXT = TEXT_TEXT
    TEXT_TAG = TEXT_TAG

    def __init__(self):
        types.ModuleType.__init__(self, "renpy")
        self.random = Rng()
        self.images = set()
        self.sim = None

    def image(self, name, d):
        if isinstance(name, str):
            name = tuple(name.split())
        self.images.add(tuple(name))

    def show(self, name, *a, **k):
        if isinstance(name, str):
            name = tuple(name.split())
        if tuple(name) not in self.images:
            raise SimError("renpy.show: нет картинки %r" % (name,))

    def hide(self, name, *a, **k):
        pass

    def say(self, who, what, *a, **k):
        self.sim.say(who, what)

    def display_menu(self, items, *a, **k):
        return self.sim.display_menu(items)

    def call_screen(self, name, *a, **k):
        return self.sim.call_screen(name, a, k)

    def input(self, prompt, default="", length=None, exclude="{}", **k):
        v = self.random.choice(["Саша", "Айдана", "", "  Ерлан  ", "Макс{}[x]"])
        return "".join(c for c in v if c not in exclude)[:length or 999]

    def full_restart(self):
        raise SimError("full_restart")


renpy = RenpyStub()
config = types.SimpleNamespace(tag_transform={}, custom_text_tags={})
S.update(dict(renpy=renpy, config=config, persistent=Persistent(), store=store,
              Character=Character, Fixed=Disp, Solid=Disp, Text=Disp, Dissolve=Disp,
              Return=Action, Hide=Action, Show=Action, NullAction=Action, _return=None))


# ---------------------------------------------------------------- text

KNOWN_TAGS = {"b", "i", "u", "s", "plain", "a", "alpha", "alt", "noalt", "art", "color", "cps",
              "done", "fast", "font", "image", "k", "nw", "outlinecolor", "p", "rb", "rt",
              "shader", "size", "space", "vspace", "w", "clear", "#"}
FMT = string.Formatter()


def interpolate(text, scope):
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "[":
            if text.startswith("[[", i):
                out.append("[")
                i += 2
                continue
            d, j = 0, i
            while j < len(text):
                if text[j] == "[":
                    d += 1
                elif text[j] == "]":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            if j >= len(text):
                raise SimError("незакрытая [ в тексте: %r" % text)
            field = text[i + 1:j]
            spec = conv = None
            m = re.match(r"^(.*?)(![a-z]+)?(:[^\]]*)?$", field)
            name = m.group(1)
            try:
                val, _ = FMT.get_field(name, (), scope)
            except Exception as e:
                raise SimError("подстановка [%s] в %r: %s: %s" % (field, text, type(e).__name__, e))
            if m.group(3):
                val = format(val, m.group(3)[1:])
            out.append(str(val))
            i = j + 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def tokenize_tags(text):
    toks = []
    i = 0
    buf = ""
    while i < len(text):
        if text.startswith("{{", i):
            buf += "{"
            i += 2
        elif text[i] == "{":
            j = text.find("}", i)
            if j < 0:
                raise SimError("незакрытый текст-тег: %r" % text)
            if buf:
                toks.append((TEXT_TEXT, buf))
                buf = ""
            toks.append((TEXT_TAG, text[i + 1:j]))
            i = j + 1
        else:
            buf += text[i]
            i += 1
    if buf:
        toks.append((TEXT_TEXT, buf))
    return toks


def render_tags(text):
    toks = tokenize_tags(text)
    out = []
    i = 0
    while i < len(toks):
        kind, val = toks[i]
        if kind == TEXT_TAG:
            name = val.split("=", 1)[0].lstrip("/")
            if name in config.custom_text_tags and not val.startswith("/"):
                arg = val.split("=", 1)[1] if "=" in val else ""
                contents = []
                i += 1
                while i < len(toks) and toks[i] != (TEXT_TAG, "/" + name):
                    contents.append(toks[i])
                    i += 1
                if i >= len(toks):
                    raise SimError("тег {%s} без {/%s}: %r" % (name, name, text))
                res = config.custom_text_tags[name](name, arg, contents)
                out.extend(v for k, v in res if k == TEXT_TEXT)
            elif name in KNOWN_TAGS:
                pass
            else:
                raise SimError("неизвестный текст-тег {%s} в %r" % (val, text))
        else:
            out.append(val)
        i += 1
    return "".join(out)


def show_text(text, scope):
    return render_tags(interpolate(text, scope))


# ---------------------------------------------------------------- screens

SCREENS = {}
DISPLAYABLES = {"text", "textbutton", "add", "null", "frame", "vbox", "hbox", "grid", "vpgrid",
                "fixed", "viewport", "window", "button", "imagebutton", "bar", "vbar", "label",
                "input", "side", "key", "timer"}


def first_expr(s):
    """Самый длинный префикс строки, который компилируется как выражение Python."""
    toks = s.split(" ")
    for n in range(len(toks), 0, -1):
        cand = " ".join(toks[:n])
        try:
            compile(cand, "<e>", "eval")
            return cand, " ".join(toks[n:])
        except SyntaxError:
            continue
    raise SimError("не разобрать выражение: %r" % s)


class Scope(dict):
    def __missing__(self, k):
        if k in S:
            return S[k]
        raise KeyError(k)


def ev(expr, scope):
    return eval(expr, S, scope)


def run_screen(name, args=(), kwargs=None, transclude=None, caller_scope=None):
    node = SCREENS[name]
    m = re.match(r"screen\s+(\w+)\s*(\((.*)\))?\s*:", node.text, re.S)
    scope = Scope()
    if m.group(2):
        sig = eval("lambda %s: locals()" % m.group(3), S)
        scope.update(sig(*args, **(kwargs or {})))
    return run_block(node.children, scope, transclude, caller_scope)


def run_block(nodes, scope, transclude, caller_scope):
    """Выполнить блок экрана. Вернуть число дочерних элементов (для проверки grid)."""
    count = 0
    i = 0
    while i < len(nodes):
        n = nodes[i]
        t = n.text
        head = t.split(None, 1)[0].rstrip(":")
        if t.startswith("$"):
            exec(t[1:].strip(), S, scope)
        elif head == "for":
            m = re.match(r"for\s+(.+?)\s+in\s+(.+):$", t, re.S)
            for item in ev(m.group(2), scope):
                tmp = {"__item": item}
                exec("%s = __item" % m.group(1), S, tmp)
                del tmp["__item"]
                scope.update(tmp)
                count += run_block(n.children, scope, transclude, caller_scope)
        elif head == "if":
            chain = [n]
            while i + 1 < len(nodes) and nodes[i + 1].text.split(None, 1)[0].rstrip(":") in ("elif", "else"):
                i += 1
                chain.append(nodes[i])
            for c in chain:
                h = c.text.split(None, 1)[0].rstrip(":")
                if h == "else" or ev(c.text.split(None, 1)[1].rstrip(":"), scope):
                    count += run_block(c.children, scope, transclude, caller_scope)
                    break
        elif head == "use":
            m = re.match(r"use\s+(\w+)\s*(\((.*)\))?\s*:?$", t, re.S)
            a, k = ((), {})
            if m.group(2):
                a, k = eval("(lambda *a, **k: (a, k))(%s)" % m.group(3), S, scope)
            count += run_screen(m.group(1), a, k, transclude=n.children, caller_scope=scope)
        elif head == "transclude":
            if transclude is not None:
                count += run_block(transclude, caller_scope, None, None)
        elif head in DISPLAYABLES:
            count += 1
            rest = t[len(head):].strip().rstrip(":")
            if head in ("text", "textbutton"):
                expr, props = first_expr(rest)
                val = ev(expr, scope)
                if not isinstance(val, str):
                    raise SimError("screen text не строка: %r" % (val,))
                show_text(val, Scope(scope))
                for c in n.children:
                    if c.text.startswith("action "):
                        ev(c.text[7:], scope)
                if "action " in props:
                    ev(props.split("action ", 1)[1].split(" text_style")[0], scope)
            elif head == "add":
                expr, _ = first_expr(rest)
                ev(expr, scope)
            elif head in ("grid", "vpgrid", "frame", "vbox", "hbox", "fixed", "viewport", "window", "button", "side"):
                kids = [c for c in n.children]
                props = {}
                for c in kids:
                    w = c.text.split(None, 1)
                    if w[0] not in DISPLAYABLES and w[0].rstrip(":") not in ("for", "if", "elif", "else", "use", "transclude") and not w[0].startswith("$"):
                        props[w[0]] = w[1] if len(w) > 1 else ""
                inner = run_block(kids, scope, transclude, caller_scope)
                if head == "grid":
                    cols, rows = [int(x) for x in rest.split()[:2]]
                    if inner != cols * rows and "allow_underfull" not in props:
                        raise SimError("grid %dx%d, а детей %d" % (cols, rows, inner))
                if head == "vpgrid":
                    cols = int(props.get("cols", 0) or 0)
                    if not cols or (inner % cols and "allow_underfull" not in props):
                        raise SimError("vpgrid cols=%s, детей %d — неполный ряд" % (cols, inner))
        elif head in ("elif", "else"):
            raise SimError("elif/else без if: %r" % t)
        else:
            pass  # свойства: xalign, spacing, modal, zorder, background...
        i += 1
    return count


# ---------------------------------------------------------------- script compile

CODE = []            # инструкции
LABELS = {}          # имя -> (pc, params)
INIT = []            # (prio, file, line, kind, payload)
DEFAULTS = []
IMAGES_TEXT = set()


def split_say(t):
    """'who "text"' или '"text"' -> (who, text) или None."""
    m = re.match(r'^(?:(\w+)\s+)?("(?:[^"\\]|\\.)*")\s*$', t, re.S)
    if not m:
        return None
    return m.group(1), eval(m.group(2))


def compile_block(nodes, file):
    i = 0
    while i < len(nodes):
        n = nodes[i]
        t = n.text
        loc = "%s:%d" % (file, n.line)
        if t.startswith("$"):
            CODE.append(("exec", compile(t[1:].strip(), loc, "exec"), loc))
        elif t == "python:":
            CODE.append(("exec", compile(n.raw_block(), loc, "exec"), loc))
        elif re.match(r"^if\s", t):
            chain = [n]
            while i + 1 < len(nodes) and re.match(r"^(elif\s|else:)", nodes[i + 1].text):
                i += 1
                chain.append(nodes[i])
            ends = []
            for c in chain:
                if c.text == "else:":
                    compile_block(c.children, file)
                else:
                    cond = c.text.split(None, 1)[1].rstrip(":")
                    idx = len(CODE)
                    CODE.append(["cond", compile(cond, loc, "eval"), None, loc])
                    compile_block(c.children, file)
                    ends.append(len(CODE))
                    CODE.append(["goto", None, loc])
                    CODE[idx][2] = len(CODE)
            for e in ends:
                CODE[e][1] = len(CODE)
        elif re.match(r"^while\s", t):
            start = len(CODE)
            CODE.append(["cond", compile(t[6:].rstrip(":"), loc, "eval"), None, loc])
            compile_block(n.children, file)
            CODE.append(["goto", start, loc])
            CODE[start][2] = len(CODE)
        elif t == "menu:":
            caption = None
            choices = []
            idx = len(CODE)
            CODE.append(["menu", None, choices, loc])
            ends = []
            for c in n.children:
                if not c.text.endswith(":"):
                    caption = split_say(c.text)
                    if caption is None:
                        raise SimError("%s: не разобрать подпись меню %r" % (loc, c.text))
                    continue
                m = re.match(r'^("(?:[^"\\]|\\.)*")\s*(?:if\s+(.+))?:$', c.text, re.S)
                if not m:
                    raise SimError("%s: не разобрать пункт меню %r" % (loc, c.text))
                choices.append((eval(m.group(1)), compile(m.group(2), loc, "eval") if m.group(2) else None, len(CODE)))
                compile_block(c.children, file)
                ends.append(len(CODE))
                CODE.append(["goto", None, loc])
            CODE[idx][1] = caption
            for e in ends:
                CODE[e][1] = len(CODE)
        elif t.startswith("call screen "):
            m = re.match(r"call screen\s+(\w+)\s*(\((.*)\))?$", t, re.S)
            CODE.append(("callscreen", m.group(1), m.group(3) or "", loc))
        elif t.startswith("call expression "):
            CODE.append(("call", None, compile(t[len("call expression "):], loc, "eval"), "", loc))
        elif t.startswith("call "):
            m = re.match(r"call\s+(\w+)\s*(\((.*)\))?$", t, re.S)
            CODE.append(("call", m.group(1), None, m.group(3) or "", loc))
        elif t.startswith("jump "):
            CODE.append(("jump", t.split()[1], loc))
        elif t == "return" or t.startswith("return "):
            e = t[6:].strip()
            CODE.append(("return", compile(e, loc, "eval") if e else None, loc))
        elif t.startswith("scene ") or (t.startswith("show ") and not t.startswith("show screen")):
            name = tuple(t.split()[1:])
            CODE.append(("image", name, loc))
        elif t.startswith("show screen"):
            CODE.append(("showscreen", t.split()[2], loc))
        elif t.startswith("hide screen") or t.startswith("hide ") or t == "pass" or t.startswith("window "):
            pass
        elif t.startswith("label "):
            m = re.match(r"label\s+(\w+)\s*(\((.*)\))?\s*:$", t, re.S)
            LABELS[m.group(1)] = (len(CODE), m.group(3))
            compile_block(n.children, file)
        else:
            sy = split_say(t)
            if sy is None:
                raise SimError("%s: неизвестная строка %r" % (loc, t))
            CODE.append(("say", sy[0], sy[1], loc))
        i += 1


def load():
    files = []
    for dp, dn, fn in os.walk(GAME):
        for f in fn:
            if f.endswith(".rpy") and f not in SKIP_FILES:
                rel = os.path.relpath(os.path.join(dp, f), GAME)
                files.append(rel)
    files.sort()
    for fi, rel in enumerate(files):
        root = parse_file(os.path.join(GAME, rel), rel)
        for n in root.children:
            t = n.text
            loc = "%s:%d" % (rel, n.line)
            m = re.match(r"^init\s*(-?\d+)?\s*python\s*:$", t)
            if m:
                INIT.append((int(m.group(1) or 0), fi, n.line, "python", compile(n.raw_block(), loc, "exec"), loc))
            elif t.startswith("define "):
                name, expr = t[7:].split("=", 1)
                INIT.append((0, fi, n.line, "define", (name.strip(), compile(expr.strip(), loc, "eval")), loc))
            elif t.startswith("default "):
                name, expr = t[8:].split("=", 1)
                DEFAULTS.append((name.strip(), compile(expr.strip(), loc, "eval"), loc))
            elif t.startswith("image "):
                name = tuple(t[6:].split("=")[0].split())
                INIT.append((0, fi, n.line, "image", name, loc))
            elif t.startswith("transform "):
                name = t.split()[1].rstrip(":")
                INIT.append((0, fi, n.line, "transform", name, loc))
            elif t.startswith("screen "):
                SCREENS[re.match(r"screen\s+(\w+)", t).group(1)] = n
            elif t.startswith("style ") or t.startswith("init "):
                pass
            elif t.startswith("label "):
                compile_block([n], rel)
            else:
                raise SimError("%s: верхний уровень %r" % (loc, t))
        CODE.append(("return", None, "%s:EOF" % rel))
    INIT.sort(key=lambda x: (x[0], x[1], x[2]))
    for prio, fi, line, kind, payload, loc in INIT:
        try:
            if kind == "python":
                exec(payload, S)
            elif kind == "define":
                exec("%s = __v" % payload[0], S, {"__v": eval(payload[1], S)}) if "." in payload[0] else S.__setitem__(payload[0], eval(payload[1], S))
            elif kind == "image":
                renpy.images.add(payload)
            elif kind == "transform":
                S[payload] = Disp()
        except Exception as e:
            raise SimError("init %s: %s: %s" % (loc, type(e).__name__, e))


# ---------------------------------------------------------------- runtime

class Bot:
    def __init__(self, seed, style):
        self.rng = random.Random(seed)
        self.style = style

    PREFER = {
        "diligent": ["Встать", "Пойти", "Слушать", "Сделать домашку", "Учиться самому", "Вернуть хозяину",
                     "Скинуться", "Выйти и решать", "Решать", "Поговорить", "Прийти с подарком"],
        "skipper": ["Поспать ещё", "Прогулять", "В курилку", "Уйти домой", "Поиграть", "Взять", "Списать",
                    "Валяться дома", "Не пойти"],
        "social": ["Поговорить", "Позвать", "Телефон", "Прийти с подарком", "Поехать", "Ответить",
                   "Обсудить", "Подсказать", "Уступить", "Встать", "Пойти", "Сделать домашку"],
    }

    def pick(self, texts, where=""):
        if where == "Что дальше?":
            return None
        if self.style == "sensible":
            i = self.sensible(texts, where)
            if i is not None:
                return i
            return self.rng.randrange(len(texts))
        pref = self.PREFER.get(self.style, [])
        if pref and self.rng.random() < 0.8:
            for p in pref:
                for i, t in enumerate(texts):
                    if t.startswith(p) or ("«" + p) in t:
                        return i
        return self.rng.randrange(len(texts))


    def find(self, texts, *prefixes):
        for p in prefixes:
            for i, t in enumerate(texts):
                if t.startswith(p):
                    return i
        return None

    def sensible(self, texts, cap):
        """Разумный игрок: смотрит на мораль, усталость и деньги, как живой человек."""
        st, r = S["stats"], self.rng.random()
        mor, fat, money = st["morale"], st["fatigue"], S["money"]
        f = lambda *p: self.find(texts, *p)
        if cap.startswith("Пара "):
            if fat >= 85 and r < 0.5:
                return f("Прогулять")
            if f("Зайти и заниматься своим") is not None and r < 0.3:
                return f("Зайти и заниматься своим")
            return f("Пойти")
        if f("Встать") is not None:
            return f("Поспать ещё") if fat >= 80 else f("Встать")
        if f("Слушать") is not None:
            return f("Поспать") if fat >= 60 else f("Слушать")
        if cap.startswith("Куда пойти?"):
            return f("В столовую")
        if cap.startswith("Что делать?"):
            if mor < 30 and money >= 1 and r < 0.5:
                return f("Буфет")
            if f("Поговорить") is not None and r < 0.75:
                return f("Поговорить")
            return f("Отдохнуть")
        if cap.startswith("Буфет"):
            if mor < 40:
                return f("Булочка")
            if fat > 70:
                return f("Энергетик")
            return f("Ничего")
        if cap in ("Пары кончились. Куда?", "Ты уже дома. Что дальше?"):
            if f("На работу") is not None and (money < 12 or r < 0.5):
                return f("На работу")
            if f("В качалку") is not None and fat < 60:
                return f("В качалку")
            if f("Купить абонемент") is not None:
                return f("Купить абонемент")
            return 0
        if cap.startswith("Вечер."):
            if f("Телефон") is not None and r < 0.4:
                return f("Телефон")
            if mor < 35:
                i = f("Позвать")
                return i if i is not None else f("Поиграть")
            if fat >= 75:
                return f("Лечь пораньше")
            if f("Сделать домашку") is not None:
                return f("Сделать домашку")
            return f("Учиться самому") if r < 0.5 else f("Поиграть")
        if cap.startswith("Воскресенье, день"):
            if f("Сделать домашку") is not None and mor >= 35:
                return f("Сделать домашку")
            if mor < 50:
                opts = [i for i in (f("Позвать"), f("Погулять"), f("Поиграть")) if i is not None]
                return self.rng.choice(opts)
            if fat >= 70:
                return f("Валяться дома")
            opts = [i for i in (f("Учиться самому"), f("Погулять"), f("В качалку"), f("Смена")) if i is not None]
            return self.rng.choice(opts)
        return None


class Sim:
    def __init__(self, seed, style, weeks, female=None):
        self.bot = Bot(seed, style)
        self.weeks = weeks
        renpy.random.seed(seed)
        renpy.sim = self
        self.seen_text = collections.Counter()
        self.says = 0
        self.hud = False
        self.female = female
        self.log = []
        self.days = []
        self.act = [w.strip() for w in os.environ.get("ACT", "").split(",") if w.strip()]

    # --- save check
    def check_save(self, where):
        if os.environ.get("NOSAVE"):
            return
        for k, v in list(S.items()):
            if k in self.base and self.base[k] is v:
                continue
            if k.startswith("__") or isinstance(v, types.ModuleType):
                continue
            try:
                pickle.dumps(v, protocol=2)
            except Exception as e:
                raise SimError("сохранение упадёт (%s): переменная %s = %r: %s" % (where, k, v, e))

    def scope(self):
        return Scope()

    def say(self, who, what, loc="renpy.say"):
        if who is not None and not isinstance(who, Character):
            raise SimError("%s: говорящий не Character: %r" % (loc, who))
        txt = show_text(what, self.scope())
        self.seen_text[txt] += 1
        self.says += 1
        self.after_interaction(loc)

    def after_interaction(self, loc):
        self.check_save(loc)
        if self.hud:
            run_screen("hud")
            if self.bot.rng.random() < 0.05:
                run_screen(self.bot.rng.choice(["profile", "people"]))
                run_screen("schedule_view", (), {"morning": False})

    def display_menu(self, items):
        opts = [(show_text(t, self.scope()), v) for t, v in items]
        live = [(t, v) for t, v in opts if v is not None]
        if not live:
            raise SimError("display_menu без вариантов")
        self.after_interaction("display_menu")
        vals = [v for t, v in live]
        if self.bot.style in ("sensible", "social") and self.bot.rng.random() < 0.7:
            good = S.get("good")
            if good in vals and set(vals) <= set(S["REPLY_TEXT"]):
                return good
            q = S.get("q")
            if q and q[1][0] in vals:
                return q[1][0]
        if self.bot.style == "sensible":
            names = [t for t, v in live]
            k = self.bot.find(names, "Передумать", "Просто покурить", "Убрать")
            if k is not None and len(live) > 1:
                live = [x for j, x in enumerate(live) if j != k]
        i = self.bot.pick([t for t, v in live])
        return live[i][1]

    def snapshot(self):
        st = S["stats"]
        log = S.get("day_log", [])
        self.days.append(dict(
            abs_day=S.get("abs_day"), week=S.get("week"), day=S.get("day"), gruzin=S.get("gruzin_week"),
            stats={k: round(v, 1) for k, v in st.items()}, money=S.get("money"),
            rels={p: S["rels"].get(p, 0) for p in S["STUDENT_ORDER"]},
            teachers={t: S["rels"].get(t, 0) for t in S["TEACHERS"]},
            n1_step=S.get("n1_step"), events=S.get("events_today"),
            zero_days=S.get("zero_morale_days"), job=S.get("has_job"), job_rate=S.get("job_rate"),
            gym=S.get("gym_pass"), smoking=S.get("has_smoking"),
            overslept=any(x.startswith(("Проспал", "Проспала")) for x in log),
            hw_ok=sum(1 for x in log if x.startswith(("Сдал ", "Сдала "))),
            hw_fail=sum(1 for x in log if x.startswith(("Не сдал", "Не сдала", "Не знал", "Не знала"))),
            hw_given=sum(1 for x in log if x.startswith("Задали домашку")),
            skips=sum(1 for p in S.get("schedule", []) if p.get("status") == "прогул") if not S["is_sunday"]() else 0,
        ))

    def call_screen(self, name, args, kwargs):
        if name == "day_summary":
            self.snapshot()
        run_screen(name, args, kwargs)
        self.after_interaction("screen " + name)
        if name == "phone":
            c = kwargs.get("contacts") or args[0]
            return self.bot.rng.choice(list(c) + [None])
        return None

    def run(self):
        S["_return"] = None
        for name, expr, loc in DEFAULTS:
            try:
                S[name] = eval(expr, S)
            except Exception as e:
                raise SimError("default %s: %s" % (loc, e))
        self.base = dict(S)  # всё, что есть после init — «константы»; сохраняется то, что поменялось
        for name, _, _ in DEFAULTS:
            self.base.pop(name, None)
        pc = LABELS["start"][0]
        stack = []
        steps = 0
        weeks_done = 0
        while True:
            steps += 1
            if steps > 400000:
                raise SimError("зацикливание? 400000 шагов")
            ins = CODE[pc]
            op = ins[0]
            loc = ins[-1]
            try:
                if op == "exec":
                    exec(ins[1], S)
                    pc += 1
                elif op == "cond":
                    pc = pc + 1 if eval(ins[1], S) else ins[2]
                elif op == "goto":
                    pc = ins[1]
                elif op == "say":
                    who = S[ins[1]] if ins[1] else None
                    self.say(who, ins[2], loc)
                    pc += 1
                elif op == "menu":
                    cap, choices = ins[1], ins[2]
                    if cap:
                        self.say(S[cap[0]] if cap[0] else None, cap[1], loc)
                    live = [(show_text(t, self.scope()), tgt) for t, c, tgt in choices if c is None or eval(c, S)]
                    if not live:
                        raise SimError("%s: меню без доступных пунктов" % loc)
                    capt = cap[1] if cap else ""
                    if self.act and ("Что дальше?" in capt or "Какую неделю" in capt):
                        n = weeks_done if "Какую неделю" in capt else weeks_done + 1
                        if "Что дальше?" in capt:
                            weeks_done += 1
                        if n >= len(self.act):
                            want = "В главное меню"
                        elif "Какую неделю" in capt:
                            want = "Неделя Грузина" if self.act[n].startswith("г") else "Обычная"
                        else:
                            want = "Прожить ещё неделю (неделя Грузина)" if self.act[n].startswith("г") else "Прожить ещё неделю (обычную)"
                        i = [k for k, (t, _) in enumerate(live) if t.startswith(want)][0]
                    elif "Что дальше?" in capt:
                        want = "Прожить ещё неделю" if weeks_done + 1 < self.weeks else "В главное меню"
                        if self.bot.rng.random() < 0.3:
                            want = "Экзамен Грузина"
                        if not want.startswith("Экзамен"):
                            weeks_done += 1
                        idx = [i for i, (t, _) in enumerate(live) if t.startswith(want)]
                        i = self.bot.rng.choice(idx)
                    elif "Кто ты?" in capt and self.female is not None:
                        i = [k for k, (t, _) in enumerate(live) if t == ("Девушка" if self.female else "Парень")][0]
                    else:
                        ## Подпись с подстановкой: иначе «[where_q]» не совпадёт с «Пары кончились. Куда?».
                        i = self.bot.pick([t for t, _ in live], show_text(capt, self.scope()))
                    self.log.append((loc, live[i][0]))
                    pc = live[i][1]
                elif op == "callscreen":
                    a, k = eval("(lambda *a, **k: (a, k))(%s)" % ins[2], S)
                    S["_return"] = self.call_screen(ins[1], a, k)
                    pc += 1
                elif op == "call":
                    name = ins[1] or eval(ins[2], S)
                    if name not in LABELS:
                        raise SimError("%s: нет label %r" % (loc, name))
                    target, params = LABELS[name]
                    saved = {}
                    if params is not None or ins[3]:
                        a, k = eval("(lambda *a, **k: (a, k))(%s)" % ins[3], S)
                        vals = eval("lambda %s: locals()" % (params or ""), S)(*a, **k)
                        for n, v in vals.items():
                            saved[n] = S.get(n, KeyError)
                            S[n] = v
                    stack.append((pc + 1, saved))
                    pc = target
                elif op == "jump":
                    pc = LABELS[ins[1]][0]
                elif op == "return":
                    S["_return"] = eval(ins[1], S) if ins[1] else None
                    if not stack:
                        return weeks_done
                    pc, saved = stack.pop()
                    for n, v in saved.items():
                        if v is KeyError:
                            S.pop(n, None)
                        else:
                            S[n] = v
                elif op == "image":
                    if ins[1] not in renpy.images:
                        raise SimError("%s: нет картинки %r" % (loc, ins[1]))
                    pc += 1
                elif op == "showscreen":
                    self.hud = True
                    run_screen(ins[1])
                    pc += 1
                else:
                    raise SimError("op %r" % op)
            except SimError as e:
                raise SimError("%s: %s" % (loc, e))
            except Exception as e:
                raise SimError("%s: %s: %s\n%s" % (loc, type(e).__name__, e, traceback.format_exc(limit=3)))


def fresh_store():
    """Сбросить store к состоянию после init (между прогонами)."""
    for k in list(S):
        if k not in INIT_STATE:
            del S[k]
    S.update(INIT_STATE)


if __name__ == "__main__":
    load()
    import copy
    for kv in filter(None, os.environ.get("OVERRIDE", "").split(",")):
        k, v = kv.split("=")
        S[k] = eval(v)
    INIT_STATE = dict(S)
    INIT_COPY = {k: copy.deepcopy(v) for k, v in S.items()
                 if isinstance(v, (dict, list, set)) and k not in ("__builtins__",)}
    MARKS = [0]
    EVCOUNT = collections.Counter()
    metrics = []
    _orig_mark = S["mark_event"]
    def _mark(eid):
        MARKS[0] += 1
        EVCOUNT[eid] += 1
        return _orig_mark(eid)
    S["mark_event"] = _mark
    INIT_STATE["mark_event"] = _mark
    runs = int(os.environ.get("RUNS", "60"))
    weeks = int(os.environ.get("WEEKS", "4"))
    fails = 0
    texts = collections.Counter()
    stats_out = []
    for r in range(runs):
        fresh_store()
        for k, v in INIT_COPY.items():
            S[k] = copy.deepcopy(v)
        styles = os.environ.get("STYLE", "random,diligent,skipper,social,sensible").split(",")
        style = styles[r % len(styles)]
        fem = {"1": True, "0": False}.get(os.environ.get("FEMALE", ""), r % 2 == 1)
        sim = Sim(1000 + r, style, weeks, female=fem)
        MARKS[0] = 0
        EVCOUNT.clear()
        try:
            wd = sim.run()
            stats_out.append((style, S.get("abs_day", S["day"]), S.get("gave_up"), {k: int(v) for k, v in S["stats"].items()},
                              S["money"], MARKS[0], S["n1_step"]))
            if os.environ.get("METRICS"):
                sim.snapshot()
                metrics.append(dict(run=r, style=style, seed=1000 + r, female=fem, gave_up=bool(S.get("gave_up")),
                                    exam_level=S["exam_level"]("gruzin"), exam_diff=S["exam_diff"].get("gruzin", 0),
                                    events=dict(EVCOUNT), days=sim.days))
        except SimError as e:
            fails += 1
            print("RUN %d (%s, seed %d) FAIL: %s" % (r, style, 1000 + r, e))
            print("   последние выборы:", sim.log[-5:])
        texts.update(sim.seen_text)
    print("прогонов: %d, упало: %d" % (runs, fails))
    by = collections.defaultdict(list)
    for st in stats_out:
        by[st[0]].append(st)
    for style, lst in sorted(by.items()):
        gu = [x for x in lst if x[2]]
        print("  %-9s n=%d  «Ушёл сам»: %d (%.0f%%), в среднем на день %.1f | ивентов в день %.2f | линия шаг≥2: %d"
              % (style, len(lst), len(gu), 100.0 * len(gu) / len(lst),
                 sum(x[1] for x in gu) / max(1, len(gu)),
                 sum(x[5] for x in lst) / float(sum(x[1] for x in lst)),
                 len([x for x in lst if x[6] >= 2])))
    if os.environ.get("VERBOSE"):
        for s in stats_out[:12]:
            print("  ", s)
    if os.environ.get("METRICS"):
        import json
        with open(os.environ["METRICS"], "w", encoding="utf8") as f:
            for m in metrics:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        print("метрики по дням: %s (%d прогонов)" % (os.environ["METRICS"], len(metrics)))
    if os.environ.get("DUMP"):
        with open(os.environ["DUMP"], "w", encoding="utf8") as f:
            for t, c in sorted(texts.items()):
                f.write("%5d  %s\n" % (c, t))
