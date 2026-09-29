## Тестовая линия №1 (одногруппница №1, отличница). 3 шага.
## 1 — первый разговор на перерыве: знакомство.
## 2 — отношения ≥ 30, перерыв: просит помочь с задачей (помочь тратит перерыв).
## 3 — отношения ≥ 45 и на шаге 2 помог, вечерняя встреча: вместе делаете домашку.
##     Созрел — она зовёт сама (line_n1_invite), можно и позвать её самому.

default n1_step = 0          # сколько шагов пройдено
default n1_helped = False
default n1_line_done = False  # флаг линии
default n1_invite_day = -99   # когда Айгерим сама звала на шаг 3 (abs_day)

## Шаг 3 созрел — Айгерим зовёт сама, не чаще раза в N дней. Иначе шаг 3
## видит только тот, кто сам догадался позвать её вечером (порог скрыт от игрока).
define N1_INVITE_EVERY = 2

init python:
    def line_ripe(pid, where="break"):
        """Созрел ли шаг линии у этого человека в этом слоте."""
        if pid != "n1" or line_steps_today >= LINE_STEPS_PER_DAY:
            return False
        if where == "break":
            if n1_step == 0:
                return True
            if n1_step == 1 and rel_value("n1") >= 30:
                return True
        if where == "evening":
            return n1_step == 2 and n1_helped and rel_value("n1") >= 45
        return False


label line_n1_step:
    if n1_step == 0:
        jump line_n1_1
    elif n1_step == 1:
        jump line_n1_2
    else:
        jump line_n1_3


label line_n1_1:
    $ was_met = met("n1")
    $ meet("n1")
    $ n1_step = 1
    if was_met:
        ## Уже виделись в ивенте — не знакомимся второй раз.
        $ say_as("n1", "А, [hero_name]. Мы уже пересекались. Нормально так и не поговорили — я Айгерим, я тут всех по списку знаю.")
    else:
        $ say_as("n1", "Ты {g=новенькая}новенький{/g}? [hero_name], да? Двадцать седьмой номер в списке. Я Айгерим, я тут всех по списку знаю.")
    $ say_as("n1", "Скажу сразу: я не люблю, когда опаздывают и болтают на парах.")
    menu:
        "«{g=Поняла}Понял{/g}. Постараюсь не мешать»":
            $ rel("n1", +M)
            $ say_as("n1", "Посмотрим.")
        "«А если болтать по делу?»":
            $ say_as("n1", "По делу — можно. Проверим.")
    return


label line_n1_2:
    $ n1_step = 2
    $ say_as("n1", "Слушай… Я застряла на задаче. Глупо, да? Посмотришь со мной?")
    menu:
        "Помочь (займёт весь перерыв)":
            $ n1_helped = True
            $ rel("n1", +S)
            $ change("know", +M)
            $ break_actions = 1   # после вычета в цикле станет 0: перерыв потрачен
            "Вы сидите над задачей до звонка. В конце она всё-таки сходится."
            $ say_as("n1", "Спасибо. Правда.")
        "Отказать: «Прости, не сейчас»":
            $ rel("n1", -M)
            $ say_as("n1", "Ладно. Сама разберусь.")
    return


## Вечер: шаг 3 созрел — она пишет сама (mehmat-framework.md, 2.3: созревший шаг показываем в слоте).
## Вернуть True — вечер потрачен.
label line_n1_invite:
    $ n1_invite_day = abs_day
    $ renpy.show("plate n1")
    "Телефон вибрирует. [n1_name]."
    $ say_as("n1", "Ты сегодня {g=свободна}свободен{/g}? Посидим в библиотеке над домашкой?")
    menu:
        "Пойти в библиотеку (займёт вечер)":
            $ line_steps_today += 1
            call line_n1_step
            $ renpy.hide("plate")
            return True
        "«Сегодня не получится»":
            $ say_as("n1", "Ладно. Тогда в другой раз.")
    $ renpy.hide("plate")
    return False


label line_n1_3:
    $ n1_step = 3
    $ n1_line_done = True
    "Вы с [n1_name] сидите в библиотеке. Перед вами одна домашка на двоих."
    $ todo = known_todo()
    python:
        undone = [h for h in todo if not h["done"]]
        if undone:
            undone[0]["done"] = True
    if undone:
        "Твоя домашка тоже готова — вдвоём быстрее."
    $ rel("n1", +S)
    $ change("morale", +S)
    $ change("know", +S)
    $ change("fatigue", +M)
    $ say_as("n1", "Слушай, а с тобой нормально заниматься. Давай так почаще.")
    $ day_log.append("Линия №1: вы с Айгерим теперь занимаетесь вместе.")
    return

define n1_name = "Айгерим"
