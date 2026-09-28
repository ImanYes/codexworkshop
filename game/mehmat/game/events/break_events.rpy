## Ивенты на перерыве и при прогуле: «Последняя булочка», «Забытый конспект»,
## «Староста собирает деньги», «Слух об отчислении», «Объявление о подработке»,
## «Угостили сигаретой».

init python:
    def smokers_here():
        pool = present if present else arrived
        return [p for p in pool if smokes(p)]

    add_event("last_bun", "break", "ev_last_bun", "Последняя булочка",
              cond=lambda: len(present) > 0)
    add_event("lost_notes", "break", "ev_lost_notes", "Забытый конспект",
              cond=lambda: len(present) > 0)
    add_event("headman_money", "break", "ev_headman_money", "Староста собирает деньги",
              cond=lambda: "n6" in present, cooldown=4)
    add_event("rumor", "break", "ev_rumor", "Слух об отчислении", once=True)
    add_event("job_ad", "break", "ev_job_ad", "Объявление о подработке",
              cond=lambda: not has_job, once=True)
    add_event("offer_cig", "break", "ev_offer_cig", "Угостили сигаретой",
              cond=lambda: not has_smoking and len(smokers_here()) > 0)
    add_event("offer_cig_skip", "skip", "ev_offer_cig", "Угостили сигаретой",
              cond=lambda: not has_smoking and len(smokers_here()) > 0)


label ev_last_bun:
    $ nb = renpy.random.choice(present)
    $ nbname = who(nb)
    scene bg canteen
    $ renpy.show("plate " + nb)
    "В буфете осталась одна булочка. [nbname] тянется к ней одновременно с тобой."
    menu:
        "Уступить":
            $ rel(nb, +S)
            $ change("morale", -M)
            "[nbname]: «О, спасибо!»"
        "Забрать ($1)" if money >= 1:
            $ money_add(-1)
            $ change("morale", +S)
            $ rel(nb, -S)
            "Булочка твоя. [nbname] смотрит с укором."
    $ renpy.hide("plate")
    scene bg corridor
    return


label ev_lost_notes:
    $ nb = renpy.random.choice(present)
    $ nbname = who(nb)
    "На подоконнике лежит чей-то конспект. Подписан: [nbname]."
    menu:
        "Вернуть хозяину":
            $ rel(nb, +S)
            "[nbname] облегчённо выдыхает: «Я уже думал(а), всё, потерял(а)!»"
        "Сначала сфоткать себе, потом вернуть":
            $ change("know", +S)
            if roll(30):
                $ rel(nb, -S)
                "[nbname] видит, как ты фоткаешь. «Мог(ла) бы и спросить»."
            else:
                $ rel(nb, +M)
                "Никто не заметил. Конспект вернулся к хозяину."
    return


label ev_headman_money:
    $ renpy.show("plate n6")
    $ hname = who("n6")
    "[hname] (староста) обходит группу: «Скидываемся по доллару на подарок куратору»."
    menu:
        "Скинуться ($1)" if money >= 1:
            $ money_add(-1)
            $ change("rep", +M)
            $ rel("n6", +M)
        "Сказать, что денег нет":
            $ change("rep", -M)
            "[hname] записывает что-то в блокнот."
    $ renpy.hide("plate")
    return


label ev_rumor:
    "Кто-то в коридоре «точно слышал»: после сессии отчислят половину курса."
    menu:
        "Обсудить с ребятами":
            $ change("morale", -S)
            python:
                for p in present:
                    rel(p, +M)
            "Паникуете вместе. Зато вместе."
        "Отмахнуться":
            $ change("morale", -M)
            "Ты делаешь вид, что тебе всё равно. Но мысль засела."
    return


label ev_job_ad:
    "На доске объявлений: «Нужен помощник в копицентр. После пар, оплата каждый день»."
    menu:
        "Позвонить и устроиться":
            $ has_job = True
            $ job_rate = 4
            $ day_log.append("Нашёл подработку: $4 за день.")
            "Тебя берут. Выходить после пар, когда хочешь. Но пропуск — ставка ниже."
        "Пройти мимо":
            "Не сейчас."
    return


label ev_offer_cig:
    $ sm = renpy.random.choice(smokers_here())
    $ smname = who(sm)
    $ renpy.show("plate " + sm)
    "[smname] протягивает пачку: «Будешь?»"
    menu:
        "Взять":
            $ has_smoking = True
            $ smoking_day = day
            $ rel(sm, +M)
            $ day_log.append("Навык: курение (курилка открыта).")
            "Ты кашляешь. [smname] смеётся. Теперь тебе есть дорога в курилку."
        "Отказаться":
            "«Как хочешь»."
    $ renpy.hide("plate")
    return
