## Ивенты на паре: «К доске!», «Самостоятельная без предупреждения»,
## «Вы меня слышите?», «Сосед просит подсказать».

init python:
    def on_normal_pair():
        return (cur_pair is not None and cur_mode == "normal"
                and cur_pair["teacher"] != "fizruk")

    add_event("board", "pair", "ev_board", "К доске!",
              cond=lambda: on_normal_pair() and not cur_pair["zoom"])
    add_event("surprise_test", "pair", "ev_surprise_test", "Самостоятельная без предупреждения",
              cond=lambda: on_normal_pair() and cur_pair["kind"] == "семинар")
    add_event("zoom_hear", "pair", "ev_zoom_hear", "Вы меня слышите?",
              cond=lambda: cur_pair is not None and cur_pair["zoom"], weight=15)
    add_event("neighbor_hint", "pair", "ev_neighbor_hint", "Сосед просит подсказать",
              cond=lambda: on_normal_pair() and not cur_pair["zoom"] and len(arrived) > 0)


label ev_board:
    $ tname = who(cur_pair["teacher"])
    "[tname] смотрит в список. «К доске!» — и называет тебя."
    menu:
        "Выйти и решать":
            if roll(20 + stats["know"]):
                "Ты пишешь решение. Мел скрипит, но всё сходится."
                $ change("rep", +M)
                $ rel(cur_pair["teacher"], +S)
            else:
                "Ты стоишь у доски и молчишь. Минута тянется очень долго."
                $ change("rep", -M)
                $ change("morale", -S)
        "Честно сказать, что не готов":
            "«Не готов». [tname] вздыхает и вызывает другого."
            $ rel(cur_pair["teacher"], -M)
    return


label ev_surprise_test:
    $ tname = who(cur_pair["teacher"])
    $ helpers = [p for p in arrived if tier(p) >= 2]
    "[tname]: «Достали листочки. Самостоятельная. Двадцать минут»."
    menu:
        "Решать самому":
            if roll(10 + stats["know"]):
                "Кажется, всё решил."
                $ rel(cur_pair["teacher"], +S)
                $ change("know", +M)
            else:
                "Половина задач так и осталась пустой."
                $ rel(cur_pair["teacher"], -M)
                $ change("morale", -M)
        "Списать у соседа" if helpers:
            $ h = renpy.random.choice(helpers)
            $ hname = who(h)
            "[hname] чуть сдвигает листок в твою сторону."
            if roll(30):
                "«Так. Два одинаковых листочка». Обоим минус."
                $ rel(cur_pair["teacher"], -S)
                $ change("rep", -S)
                $ rel(h, -M)
            else:
                "Прокатило."
                $ rel(cur_pair["teacher"], +M)
                $ rel(h, +M)
    return


label ev_zoom_hear:
    gr "Так. Следующий. …Вы меня слышите?"
    "Он назвал тебя. Микрофон выключен."
    menu:
        "Судорожно искать кнопку микрофона":
            if roll(50):
                "«Да, слышу!» — успел."
                gr "Хорошо. Отвечайте."
            else:
                "Пока ищешь кнопку, проходит вечность. В чате группы — сплошные смайлики."
                gr "Ясно. Следующий."
                $ rel("gruzin", -M)
                $ change("morale", +M)
        "Написать в чат «Простите, микрофон сломался»":
            gr "Сломался. Конечно."
            $ rel("gruzin", -M)
    return


label ev_neighbor_hint:
    $ nb = renpy.random.choice(arrived)
    $ nbname = who(nb)
    $ renpy.show("plate " + nb)
    "[nbname] толкает тебя локтем: «Слушай, что тут в третьем пункте?»"
    menu:
        "Подсказать шёпотом":
            $ rel(nb, +S)
            if roll(25):
                "Препод поднимает голову. «Разговоры!» Смотрит прямо на тебя."
                $ rel(cur_pair["teacher"], -M)
                $ change("rep", -M)
            else:
                "[nbname] благодарно кивает."
        "Сделать вид, что не слышишь":
            $ rel(nb, -M)
            "[nbname] обиженно отворачивается."
    return
