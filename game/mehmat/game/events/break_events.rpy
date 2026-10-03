## Ивенты на перерыве и при прогуле: «Последняя булочка», «Забытый конспект»,
## «Староста собирает деньги», «Слух об отчислении», «Объявление о подработке»,
## «Угостили сигаретой».

init python:
    def smokers_here():
        """Курящие рядом: на перерыве — кто рядом, на прогуле — кто прогуливает с тобой."""
        return [p for p in present if smokes(p)]

    ## Один id в нескольких слотах = один ивент: общая пауза (cooldown) и общий once.
    ## Пауза считается по сквозному дню: cooldown=4 — следующий раз не раньше чем через 4 дня.
    add_event("last_bun", "break", "ev_last_bun", "Последняя булочка",
              cond=lambda: len(present) > 0, cooldown=4)
    add_event("last_bun", "skip", "ev_last_bun", "Последняя булочка",
              cond=lambda: len(present) > 0, cooldown=4)
    add_event("lost_notes", "break", "ev_lost_notes", "Забытый конспект",
              cond=lambda: len(present) > 0, cooldown=4)
    ## Карина (n6) собирает деньги за всю группу — ей не нужно стоять рядом, достаточно прийти.
    ## Сбор не чаще раза в 10 дней: денег всего $1 в неделю.
    add_event("headman_money", "break", "ev_headman_money", "Староста собирает деньги",
              cond=lambda: "n6" in arrived, cooldown=10)
    add_event("rumor", "break", "ev_rumor", "Слух об отчислении", once=True)
    add_event("rumor", "smoke", "ev_rumor", "Слух об отчислении", once=True)
    ## Не once: отказался — объявление попадётся снова, пока нет работы.
    ## Ивенты-«открывашки» (работа, курение): первый раз — рано, повтор после отказа — реже.
    add_event("job_ad", "break", "ev_job_ad", "Объявление о подработке",
              cond=lambda: not has_job, cooldown=4)
    add_event("job_ad", "skip", "ev_job_ad", "Объявление о подработке",
              cond=lambda: not has_job, cooldown=4)
    ## Страховка: не попалось в первый день — со 2-го дня на перерыве почти наверняка
    ## (вес 100), чтобы работа была доступна до недели Грузина.
    add_event("job_ad", "break", "ev_job_ad", "Объявление о подработке",
              cond=lambda: not has_job and "job_ad" not in seen_events and abs_day >= 2,
              cooldown=4, weight=100)
    add_event("offer_cig", "break", "ev_offer_cig", "Угостили сигаретой",
              cond=lambda: not has_smoking and len(smokers_here()) > 0, cooldown=4)
    add_event("offer_cig", "skip", "ev_offer_cig", "Угостили сигаретой",
              cond=lambda: not has_smoking and len(smokers_here()) > 0, cooldown=4)


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
    $ nb_thought = sx(nb, "думал", "думала")
    $ nb_lost = sx(nb, "потерял", "потеряла")
    "На подоконнике лежит чей-то конспект. Подписан: [nbname]."
    menu:
        "Вернуть хозяину":
            $ rel(nb, +S)
            "[nbname] облегчённо выдыхает: «Я уже [nb_thought], всё, [nb_lost]!»"
        "Сначала сфоткать себе, потом вернуть":
            $ change("know", +S)
            if roll(30):
                $ rel(nb, -S)
                "[nbname] видит, как ты фоткаешь. «{g=Могла}Мог{/g} бы и спросить»."
            else:
                $ rel(nb, +M)
                "Никто не заметил. Конспект вернулся к хозяину."
    return


label ev_headman_money:
    $ renpy.show("plate n6")
    $ hname = who("n6")
    "[hname] обходит группу со списком: «Скидываемся по доллару на подарок куратору. Я записываю, кто сдал»."
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
            $ job_rate = JOB_RATE
            $ day_log.append(gf("Нашёл", "Нашла") + " подработку: ${} за день.".format(JOB_RATE))
            "Тебя берут. Смена после пар — $[JOB_RATE]. Не {g=вышла}вышел{/g} в будний день — ставка на $1 ниже, {g=вышла}вышел{/g} — снова на $1 выше (не больше $[JOB_RATE])."
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
            $ smoking_day = abs_day
            $ rel(sm, +M)
            $ day_log.append("Навык: курение (курилка открыта).")
            "Ты кашляешь. [smname] смеётся. Теперь тебе есть дорога в курилку."
        "Отказаться":
            "«Как хочешь»."
    $ renpy.hide("plate")
    return
