## Сложность экзамена у Грузина (mehmat-design.md, «Грузин»; mehmat-framework.md, 2.7).
## Главное — посещение его семинаров вживую: каждый пропущенный → +1 к сложности.
## Все семинары недели Грузина → отношения 6/10 → легче. На 7/10 — заметно легче.
## Знания тоже двигают сложность. Сам экзамен пока — тестовая заглушка вместо мини-игры.

define EXAM_WORDS = ["легко", "нормально", "тяжело", "очень тяжело"]
define EXAM_PASS_CHANCE = [90, 70, 45, 25]      # заглушка: шанс сдать по сложности

init python:

    def exam_level(tid):
        """0 легко … 3 очень тяжело."""
        lvl = 1 + exam_diff.get(tid, 0)
        r = rels.get(tid, 50)
        if r >= 70:
            lvl -= 2
        elif r >= 60:
            lvl -= 1
        elif r < 40:
            lvl += 1
        if stats["know"] >= 60:
            lvl -= 1
        elif stats["know"] < 30:
            lvl += 1
        return max(0, min(3, lvl))

    def exam_words(tid):
        return EXAM_WORDS[exam_level(tid)]


## Тест из меню конца недели. Статы не меняет — только показывает, чем бы кончилось.
label gruzin_exam_test:
    scene bg aud
    $ renpy.show("plate gruzin")
    $ lvl_word = exam_words("gruzin")
    $ missed_sem = exam_diff.get("gruzin", 0)
    "Экзамен по ангему (тест). Сложность: [lvl_word]. Пропущено семинаров вживую: [missed_sem]."
    ## Проспать экзамен можно, только если усталость 10 и мораль 0.
    if stats["fatigue"] >= 100 and shown("morale") == 0:
        "Ты {g=проспала}проспал{/g} экзамен: усталость 10, мораль 0."
        $ renpy.hide("plate")
        return
    gr "Билет. Двадцать минут. Время пошло."
    if roll(EXAM_PASS_CHANCE[exam_level("gruzin")]):
        gr "Зачётку."
        "Грузин молча ставит оценку. {g=Сдала}Сдал{/g}."
    else:
        gr "Нет. Придёте ещё раз."
        "Не {g=сдала}сдал{/g}. В настоящей игре это была бы пересдача."
    $ renpy.hide("plate")
    return
