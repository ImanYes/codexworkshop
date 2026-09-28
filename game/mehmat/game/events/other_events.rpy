## Ивенты курилки, утра, вечера, ночи и директор:
## «Параллельный поток», «Групповой чат: решённая домашка», «Звонок из дома»,
## «Сообщение в 2 ночи», «Директор в коридоре».

init python:
    add_event("parallel", "smoke", "ev_parallel", "Параллельный поток",
              cond=lambda: len(unknown_rules()) > 0, cooldown=1)
    add_event("chat_hw", "evening", "ev_chat_hw", "Групповой чат: решённая домашка",
              cond=lambda: len([h for h in known_todo() if not h["done"]]) > 0)
    add_event("call_home", "evening", "ev_call_home", "Звонок из дома", cooldown=3)
    add_event("call_home_m", "morning", "ev_call_home", "Звонок из дома", cooldown=3)
    add_event("msg_2am", "night", "ev_msg_2am", "Сообщение в 2 ночи",
              cond=lambda: any(met(p) for p in STUDENT_ORDER))
    ## Директор не выпадает из пула: у него свой шанс 5% при прогуле.
    add_event("director", "never", "ev_director", "Директор в коридоре")

## После всех add_event (init 0 во всех файлах).
init 1 python:
    EVENT_BY_ID = {e.id: e for e in EVENTS}


label ev_parallel:
    $ r = renpy.random.choice(unknown_rules())
    $ known_rules.add(r[0])
    $ rule_text = r[1]
    "Двое с параллельного потока делятся слухами."
    "«[rule_text]»"
    "Ты запоминаешь. Досье пополнилось."
    $ change("fatigue", +M)
    $ day_log.append("Узнал скрытое правило (см. профиль).")
    return


label ev_chat_hw:
    $ undone = [h for h in known_todo() if not h["done"]]
    $ h = undone[0]
    "Групповой чат: кто-то выложил решённую домашку по предмету «[h[subj]]»."
    menu:
        "Списать":
            $ h["done"] = True
            $ h["cheated"] = True
            "Пять минут — и готово. Вечер свободен… почти."
        "Не надо, сделаю сам(а)":
            "Ты закрываешь чат."
    return


label ev_call_home:
    "Звонит мама."
    mom "Ну как учёба? Кушаешь нормально?"
    $ fine = (stats["morale"] >= 50 and stats["know"] >= 30)
    menu:
        "Рассказать как есть":
            if fine:
                mom "Молодец! Мы тобой гордимся."
                $ change("morale", +S)
            else:
                mom "Ох… Ты держись. Может, приедешь на выходных?"
                $ change("morale", -S)
        "Сказать, что всё отлично":
            mom "Ну и хорошо."
            $ change("morale", +M)
            if not fine:
                "Вешаешь трубку. На душе всё равно тяжело."
                $ change("morale", -M)
    return


label ev_msg_2am:
    $ friends = [p for p in STUDENT_ORDER if met(p)]
    $ pid = renpy.random.choice(friends)
    $ pname = who(pid)
    "2:07. Телефон вибрирует. [pname]: «не спишь?»"
    menu:
        "Ответить":
            $ rel(pid, +S)
            $ change("fatigue", +M)
            "Переписываетесь до трёх. Узнаёшь о человеке много нового."
        "Спать дальше":
            "Ты переворачиваешься на другой бок."
    return


label ev_director:
    scene bg corridor
    $ renpy.show("plate director")
    dr "Так. А почему не на паре?"
    menu:
        "Сказать правду":
            dr "Честно. Ценю. Но чтобы это было в последний раз."
            $ change("rep", -M)
            $ rel("director", +M)
            $ director_honest = True
        "Соврать: «Иду в учебную часть»":
            if roll(50):
                dr "…Ну иди."
            else:
                dr "Я только что оттуда. Фамилия?"
                "Он записывает. Кажется, это надолго."
                $ rel("director", -B)
                $ change("morale", -S)
    $ renpy.hide("plate")
    return

default director_honest = False
