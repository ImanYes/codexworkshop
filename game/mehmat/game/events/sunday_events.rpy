## Воскресные ивенты: «День рождения одногруппника», «Поездка за город с группой».
## Меняют sunday_actions: день рождения занимает одно дело, поездка — весь день.

init python:
    def met_students():
        return [p for p in STUDENT_ORDER if met(p)]

    add_event("birthday", "sunday", "ev_birthday", "День рождения одногруппника",
              cond=lambda: len(met_students()) > 0, cooldown=7)
    add_event("trip", "sunday", "ev_trip", "Поездка за город с группой",
              cond=lambda: stats["rep"] >= 60 and len(met_students()) > 0, cooldown=14)


label ev_birthday:
    $ bd = renpy.random.choice(met_students())
    $ bdname = who(bd)
    $ renpy.show("plate " + bd)
    "Сообщение от [bdname]: «У меня сегодня днюха! Приходи в общагу, отмечаем»."
    menu:
        "Прийти с подарком ($1)" if money >= 1:
            $ money_add(-1)
            $ rel(bd, +S)
            $ change("morale", +S)
            $ change("fatigue", +M)
            $ sunday_actions -= 1
            "Торт, чай, кто-то принёс гитару. Подарку рады больше, чем ты {g=ждала}ждал{/g}."
        "Прийти без подарка":
            $ rel(bd, +M)
            $ change("morale", +S)
            $ change("fatigue", +M)
            $ sunday_actions -= 1
            "Ты {g=пришла}пришёл{/g} с пустыми руками, но тебе всё равно рады."
        "Не пойти":
            $ rel(bd, -M)
            "«Жаль. Ну ладно»."
    $ renpy.hide("plate")
    scene bg home
    return


label ev_trip:
    "В чате группы: «Едем за город! Электричка в 9:00, шашлыки, озеро»."
    menu:
        "Поехать ($2) — на весь день" if money >= 2:
            $ money_add(-2)
            $ change("morale", +B)
            $ change("fatigue", +S)
            python:
                for p in met_students():
                    rel(p, +M)
            $ sunday_actions = 0
            scene bg street
            "Весь день на воздухе. Домой возвращаетесь затемно, уставшие и довольные."
            scene bg home
        "Не ехать":
            $ change("morale", -M)
            "Ты остаёшься дома. В чате весь день фотки с озера."
    return
