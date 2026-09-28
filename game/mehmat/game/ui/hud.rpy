## Экраны прототипа: полоска статов, заставка дня, расписание, итог дня,
## профиль героя, карточки отношений, телефон.

style hud_text is default:
    size 30
    color "#ffffff"

style hud_button_text is default:
    size 28
    color "#b0d0ff"
    hover_color "#ffffff"

style card_title is default:
    size 48
    color "#ffd27a"

style card_text is default:
    size 32
    color "#e5e9f0"

style card_small is default:
    size 26
    color "#aab2c0"

style card_button_text is default:
    size 34
    color "#b0d0ff"
    hover_color "#ffffff"


## ----- Полоска статов: всегда на экране -----

screen hud():
    zorder 50
    frame:
        xfill True
        ypos 0
        background Solid("#000000b0")
        padding (30, 12)
        hbox:
            spacing 45
            text now_text style "hud_text" color "#ffd27a"
            text "${}".format(money) style "hud_text"
            text "Усталость {}/10".format(shown("fatigue")) style "hud_text"
            text "Мораль {}/10".format(shown("morale")) style "hud_text"
            text "Домашки: {}".format(hw_short()) style "hud_text"
    hbox:
        xalign 1.0
        ypos 64
        xoffset -30
        spacing 30
        textbutton "Расписание" action Show("schedule_view", morning=False) text_style "hud_button_text"
        textbutton "Профиль" action Show("profile") text_style "hud_button_text"
        textbutton "Люди" action Show("people") text_style "hud_button_text"


## Общая рамка для «карточек».
## zorder и modal у экрана из `use` не работают — их ставим в каждом экране-карточке.
screen card(title, width=1200):
    add Solid("#00000088")
    frame:
        xalign 0.5
        yalign 0.5
        xsize width
        background Solid("#1b1f27f0")
        padding (50, 40)
        vbox:
            spacing 14
            text title style "card_title"
            null height 6
            transclude


## ----- Заставка дня -----

screen day_card():
    modal True
    zorder 100
    add Solid("#000000")
    vbox:
        align (0.5, 0.45)
        spacing 20
        text day_title() size 60 color "#ffd27a" xalign 0.5
        if gruzin_week:
            text "Все пары — Грузин, вживую." size 32 color "#ff9090" xalign 0.5
    key "dismiss" action Return()
    timer 2.5 action Return()


## ----- Расписание -----

screen schedule_view(morning=False):
    modal True
    zorder 100
    use card("Расписание · " + weekday_name()):
        for i, p in enumerate(schedule):
            hbox:
                spacing 20
                text PAIR_TIME[i] style "card_small" min_width 200
                text pair_label(p) style "card_text"
                if p["status"]:
                    text "— " + p["status"] style "card_small" color "#88c0d0"
        null height 16
        text "Домашки" style "card_title" size 36
        if hw_list():
            for h in hw_list():
                text "• {} — до следующей пары по предмету{}".format(h["subj"], " (готово)" if h["done"] else "") style "card_text"
        else:
            text "нет" style "card_small"
        null height 16
        textbutton ("Начать день" if morning else "Закрыть"):
            text_style "card_button_text"
            action (Return() if morning else Hide("schedule_view"))


## ----- Профиль героя -----

screen profile():
    modal True
    zorder 100
    use card("Профиль"):
        text "Знания: {}/10".format(shown("know")) style "card_text"
        text "Харизма: {}/10  (итоговая {:.1f})".format(shown("cha"), total_cha()) style "card_text"
        text "Привлекательность: {}/10".format(shown("att")) style "card_text"
        text "Репутация: " + rep_words() style "card_text"
        text "Мораль: {}/10   Усталость: {}/10   Деньги: ${}".format(shown("morale"), shown("fatigue"), money) style "card_text"
        null height 10
        text "Навыки и вещи" style "card_title" size 36
        text "Курение: {}   Работа: {}   Абонемент: {}".format(
            "да" if has_smoking else "нет",
            "да, ${}/день".format(job_rate) if has_job else "нет",
            "да" if gym_pass else "нет") style "card_text"
        text "Анекдоты Василия: {} (за всё время {})".format(len(heard_anecdotes), len(persistent.anecdotes)) style "card_text"
        null height 10
        text "Досье: скрытые правила" style "card_title" size 36
        $ rules = [r[1] for r in HIDDEN_RULES if r[0] in known_rules]
        if rules:
            for r in rules:
                text "• " + r style "card_small"
        else:
            text "пока ничего не знаешь" style "card_small"
        null height 16
        textbutton "Закрыть" action Hide("profile") text_style "card_button_text"


## ----- Карточки отношений -----

screen people():
    modal True
    zorder 100
    use card("Одногруппники", 1500):
        grid 3 2:
            spacing 20
            for pid in STUDENT_ORDER:
                $ d = STUDENTS[pid]
                frame:
                    xsize 440
                    background Solid("#2a303c")
                    padding (20, 16)
                    vbox:
                        spacing 4
                        text "№{} {}".format(d["num"], d["name"]) style "card_text" color "#ffd27a"
                        text tier_name(pid) style "card_text"
                        if met(pid):
                            text d["hint"] style "card_small"
                            text ("курит" if d["smokes"] else "не курит") + ", ходит " + d["attend"] style "card_small"
                            text ("сегодня здесь" if pid in arrived else "сегодня нет") style "card_small"
                        else:
                            text "ещё не знакомы" style "card_small"
        null height 16
        text "Отношения с преподами скрыты." style "card_small"
        textbutton "Закрыть" action Hide("people") text_style "card_button_text"


## ----- Телефон -----

screen phone(contacts):
    modal True
    zorder 100
    use card("Телефон", 700):
        text "Одно сообщение за вечер. Вечер не тратит." style "card_small"
        for pid in contacts:
            textbutton "{} — {}".format(who(pid), tier_name(pid)):
                text_style "card_button_text"
                action Return(pid)
        null height 10
        textbutton "Убрать телефон" action Return(None) text_style "card_button_text"


## ----- Итог дня -----

screen day_summary():
    modal True
    zorder 100
    use card("Итог дня · " + weekday_name()):
        $ lines = summary_lines()
        for s in lines:
            text s style "card_text"
        if day_log:
            null height 10
            for s in day_log:
                text "• " + s style "card_small"
        null height 16
        textbutton "Спать" action Return() text_style "card_button_text"


## ----- Итог недели -----

screen week_summary():
    modal True
    zorder 100
    use card("Неделя прожита"):
        text "Знания {}/10 · Харизма {}/10 · Привлекательность {}/10".format(shown("know"), shown("cha"), shown("att")) style "card_text"
        text "Мораль {}/10 · Усталость {}/10 · Деньги ${}".format(shown("morale"), shown("fatigue"), money) style "card_text"
        text "Репутация: " + rep_words() style "card_text"
        for pid in STUDENT_ORDER:
            text "{}: {}".format(who(pid), tier_name(pid)) style "card_small"
        text "Линия №1: шаг {} из 3".format(n1_step) style "card_small"
        null height 10
        text "Скрыто от игрока (для теста баланса):" style "card_small" color "#ff9090"
        text "Преподы: " + ", ".join("{} {}".format(who(t), rels[t] // 10) for t in TEACHERS) style "card_small"
        text "Сложность экзамена у Грузина: +{}".format(exam_diff.get("gruzin", 0)) style "card_small"
        null height 16
        textbutton "Дальше" action Return() text_style "card_button_text"


init python:

    def summary_lines():
        """Что выросло и что упало из видимого + у кого стали лучше отношения."""
        out = []
        old = snap["stats"]
        for s in ("morale", "fatigue", "know", "cha", "att"):
            a, b = int(old[s] // 10), int(stats[s] // 10)
            if a != b:
                out.append("{}: {} → {} {}".format(STAT_NAME[s].capitalize(), a, b, "↑" if b > a else "↓"))
        if snap["money"] != money:
            out.append("Деньги: ${} → ${}".format(snap["money"], money))
        if snap["rep_words"] != rep_words():
            out.append("Репутация: " + rep_words())
        for pid in STUDENT_ORDER:
            if rels.get(pid, 0) > snap["rels"].get(pid, 0):
                out.append("{} ↑ ({})".format(who(pid), tier_name(pid)))
            elif pid in snap["rels"] and rels[pid] < snap["rels"][pid]:
                out.append("{} ↓".format(who(pid)))
        if not out:
            out.append("Ничего заметно не изменилось.")
        return out
