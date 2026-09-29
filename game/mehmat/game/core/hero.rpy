## Герой: имя и пол выбирает игрок в начале игры.
##
## Как писать текст, который зависит от пола героя:
##   в сценах:  "Ты {g=проспала}проспал{/g} всю лекцию."   — {g=женская форма}мужская форма{/g}
##   в Python:  gf("Проспал", "Проспала")                  — для строк в журнале дня и т. п.

default hero_name = "Саша"
default hero_female = False

init -10 python:

    def gf(m, f):
        """Слово в роде героя: gf("пришёл", "пришла")."""
        return f if hero_female else m

    def g_tag(tag, argument, contents):
        """Текст-тег {g=женская}мужская{/g}: Ren'Py сам подставит нужную форму."""
        if hero_female:
            return [(renpy.TEXT_TEXT, argument)]
        return contents

    config.custom_text_tags["g"] = g_tag


label hero_setup:
    menu:
        "Кто ты?"
        "Парень":
            $ hero_female = False
        "Девушка":
            $ hero_female = True
    $ hero_name = renpy.input("Как тебя зовут?", default="Саша", length=20, exclude="{}[]%").strip() or "Саша"
    "Тебя зовут [hero_name]. Первый курс мехмата. Поехали."
    return
