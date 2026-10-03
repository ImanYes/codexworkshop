## Разговоры с одногруппниками: тема → реплика персонажа → твой ответ → реакция.
## Тексты — в game/dialogues/, по файлу на человека. Как писать — game/design/dialogues.md.
##
## Итог разговора решают две вещи:
##   1) настроение собеседника — бросок talk_chance (харизма, мораль, ступень). Плохое видно сразу;
##   2) твой ответ: good — под характер, ok — нейтрально, bad — мимо (задел, бесит).

default dlg_seen = {}       # pid -> {тема: сколько сцен темы уже было}
default dlg_facts = {}      # pid -> [что герой узнал о человеке] — видно в карточке «Люди»
default dlg_good = None     # для бота-проверки: какой ответ сейчас «хороший»
default dlg_menu = False

## Сколько отношений даёт ответ: (качество, настроение хорошее?) → размер.
## "talk" — как раньше удачный разговор: С на большом перерыве, пока вы не друзья, иначе М.
## Повтор уже виденной сцены — на ступень меньше (С → М → 0). Минусы не уменьшаются.
## Числа — те же М = 1, С = 2 из core/stats.rpy (тут цифрами: этот файл грузится раньше).
define DLG_GAIN = {
    ("good", True): "talk",
    ("good", False): 1,
    ("ok", True): 1,
    ("ok", False): 0,
    ("bad", True): -1,
    ("bad", False): -2,
}

init -10 python:
    ## Сюда файлы из game/dialogues/ складывают свои тексты: DIALOGUES["n1"] = dict(...).
    DIALOGUES = {}

init python:

    def dlg(pid):
        return DIALOGUES[pid]

    def dlg_topic(pid, tid):
        for t in dlg(pid)["topics"]:
            if t["id"] == tid:
                return t
        raise Exception("Разговор: у {} нет темы {}".format(pid, tid))

    def dlg_scene(pid, tid, si):
        if tid == "intro":
            return dlg(pid)["intro"]
        return dlg_topic(pid, tid)["scenes"][si]

    def dlg_topic_items(pid):
        """Меню тем: [(подпись, id)]. Узнал факт — подпись меняется на конкретную."""
        items = []
        facts = dlg_facts.get(pid, [])
        for t in dlg(pid)["topics"]:
            if "cond" in t and not t["cond"]():
                continue
            label = t["label"]
            if t.get("reveals") in facts:
                label = t.get("label_known", label)
            items.append((label, t["id"]))
        return items

    def dlg_next_scene(pid, tid):
        """Следующая непросмотренная сцена темы. Все видел — случайная, с пометкой «повтор»."""
        seen = dlg_seen.setdefault(pid, {})
        n = seen.get(tid, 0)
        seen[tid] = n + 1
        scenes = dlg_topic(pid, tid)["scenes"]
        if n < len(scenes):
            return n, False
        return renpy.random.randrange(len(scenes)), True

    def dlg_learn(pid, tid):
        if tid == "intro":
            return
        fact = dlg_topic(pid, tid).get("reveals")
        facts = dlg_facts.setdefault(pid, [])
        if fact and fact not in facts:
            facts.append(fact)
            day_log.append("Узнал{}: {} — {}.".format(gf("", "а"), who(pid), fact))

    def dlg_line(pid, line):
        """Строка сцены: «* текст» — от автора, иначе — реплика персонажа."""
        if line.startswith("* "):
            renpy.say(None, line[2:])
        else:
            say_as(pid, line)

    def dlgdlg_options(pid, tid, si):
        """Ответы в случайном порядке, чтобы «хороший» не стоял всегда на одном месте."""
        opts = list(enumerate(dlg_scene(pid, tid, si)["options"]))
        renpy.random.shuffle(opts)
        global dlg_good, dlg_menu
        dlg_good = [i for i, o in opts if o[1] == "good"][0]
        dlg_menu = True
        return [(o[0], i) for i, o in opts]

    def dlg_apply(pid, quality, mood, big, repeat):
        size = DLG_GAIN[(quality, mood)]
        if size == "talk":
            size = S if big and tier(pid) < TALK_S_BELOW_TIER else M
        if repeat and size > 0:
            size -= 1
        if size:
            rel(pid, size)

    def dlg_rule(rule):
        """Ответ открыл скрытое правило препода — оно попадает в досье."""
        if rule and rule not in known_rules:
            known_rules.add(rule)
            day_log.append("В досье: новое скрытое правило.")


## Одна сцена: реплики персонажа → выбор ответа → реакция → отношения.
## Передаём только id — сами тексты не попадают в сохранение.
label dlg_play(pid, tid, si, mood=True, big=False, repeat=False):
    $ dlg_lines = dlg_scene(pid, tid, si)["lines"]
    $ dlg_k = 0
    while dlg_k < len(dlg_lines):
        $ dlg_line(pid, dlg_lines[dlg_k])
        $ dlg_k += 1

    $ dlg_pick = renpy.display_menu(dlgdlg_options(pid, tid, si))
    $ dlg_menu = False
    $ dlg_opt = dlg_scene(pid, tid, si)["options"][dlg_pick]

    $ dlg_lines = dlg_opt[2]
    $ dlg_k = 0
    while dlg_k < len(dlg_lines):
        $ dlg_line(pid, dlg_lines[dlg_k])
        $ dlg_k += 1

    $ dlg_apply(pid, dlg_opt[1], mood, big, repeat)
    $ dlg_rule(dlg_opt[3] if len(dlg_opt) > 3 else None)
    $ dlg_learn(pid, tid)
    return


## Обычный разговор (не шаг линии и не знакомство): настроение → тема → сцена.
label dlg_talk(pid, big=False):
    $ dlg_mood = roll(talk_chance(pid))
    if not dlg_mood:
        $ dlg_line(pid, "* " + dlg(pid)["mood_bad"])
    $ dlg_tid = renpy.display_menu(dlg_topic_items(pid))
    $ dlg_si, dlg_rep = dlg_next_scene(pid, dlg_tid)
    if dlg_rep:
        "Вы уже говорили об этом. Разговор идёт по второму кругу."
    call dlg_play(pid, dlg_tid, dlg_si, dlg_mood, big, dlg_rep)
    return


## Знакомство: своя сцена у каждого. Нет сцены — короткая строка.
label dlg_intro(pid, big=False):
    $ meet(pid)
    if "intro" in dlg(pid):
        call dlg_play(pid, "intro", 0, True, big, False)
    else:
        $ nm = who(pid)
        $ nhint = STUDENTS[pid]["hint"]
        "Новое знакомство: [nm]. [nhint]."
    return


init python:
    def dlg_phone(pid, ok):
        """Ответ на сообщение вечером — в манере персонажа."""
        lines = dlg(pid)["phone_ok" if ok else "phone_no"]
        dlg_line(pid, "* " + renpy.random.choice(lines))
