## Воскресенье — выходной (mehmat-design.md, «Воскресенье»).
## Пар нет: утро → днём два дела → вечер (как в будни) → ночь.
## Днём можно сделать домашку, поучиться, сходить в качалку, выйти на смену,
## позвать кого-то погулять или просто отдохнуть. Бывают воскресные ивенты.

default sunday_actions = 0
default sunday_refused = False      # уже отказали сегодня — второй раз не зовём

init python:

    def invite_chance(pid):
        """Шанс, что согласятся погулять в воскресенье: ступень отношений + харизма + репутация.
        Мало харизмы и репутации → скорее всего откажут (из дока)."""
        p = ({1: 30, 2: 60, 3: 80, 4: 95}[tier(pid)]
             + 5 * (total_cha() - 5)
             + (stats["rep"] - 40) / 4.0)
        return clamp(p, 5, 95)


label sunday:
    scene bg home
    $ now_text = "воскресенье · утро"
    $ arrived = []                  # в универ никто не ходит — «сегодня нет» у всех
    call screen day_card
    $ change("fatigue", -M)
    "Воскресенье. Будильник выключен — спишь до десяти."

    $ ev = take_event("morning")
    if ev:
        call expression ev

    call sunday_day
    call evening
    return


label sunday_day:
    $ now_text = "воскресенье · день"
    $ sunday_actions = 2
    scene bg home

    ## Воскресный ивент может занять одно дело или весь день.
    $ ev = take_event("sunday")
    if ev:
        call expression ev

    while sunday_actions > 0:
        scene bg home
        $ todo = known_todo()
        $ friends = [p for p in STUDENT_ORDER if met(p)]
        menu:
            "Воскресенье, день. Дел осталось: [sunday_actions]."
            "Сделать домашку" if todo:
                call do_homework
            "Учиться самому":
                call act_study
            "В качалку" if gym_pass:
                call gym
            "Купить абонемент ($10) и в качалку" if not gym_pass and money >= 10:
                call buy_gym
            "Смена на работе (+$[job_rate])" if has_job:
                call work_shift
            "Позвать кого-то погулять ($1)" if friends and money >= 1 and not sunday_refused:
                call sunday_invite(friends)
                if _return == "refused":
                    ## Отказ не тратит дело — можно выбрать другое.
                    $ sunday_actions += 1
            "Погулять по городу одному":
                call act_walk
            "Поиграть":
                call act_games
            "Валяться дома":
                $ change("fatigue", -S)
                "Сериал, чай, одеяло. Никуда не надо."
        $ sunday_actions -= 1
    return


label sunday_invite(friends):
    $ pid = renpy.display_menu([("{} — {}".format(who(p), tier_name(p)), p) for p in friends])
    $ nm = who(pid)
    $ renpy.show("plate " + pid)
    "Ты пишешь [nm]: «Пойдём погуляем?»"
    if not roll(invite_chance(pid)):
        $ busy = sx(pid, "занят", "занята")
        "[nm]: «В воскресенье? Не, я [busy]»."
        ## Отказ бьёт по самооценке и по тому, как на тебя смотрят.
        $ change("rep", -M)
        $ change("morale", -M)
        $ change("cha", -M)
        $ sunday_refused = True
        $ renpy.hide("plate")
        return "refused"
    $ money_add(-1)
    $ rel(pid, +S)
    $ change("morale", +S, boredom_factor("meet"))
    $ did_activity("meet")
    $ change("fatigue", +M)
    scene bg street
    $ renpy.show("plate " + pid)
    "[nm] соглашается. Вы гуляете по городу, едите мороженое и болтаете обо всём."
    $ renpy.hide("plate")
    return "ok"


label act_walk:
    scene bg street
    $ change("morale", +M, boredom_factor("walk"))
    $ did_activity("walk")
    $ change("fatigue", +M)
    "Ты бродишь по городу без цели. Голова проветривается."
    return
